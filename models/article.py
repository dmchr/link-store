import config
import math
import time
import web
from mq import create_job
from source import mSource

DB = config.DB


class ArticleException(Exception):
    pass


class Article:
    id = None
    url = None
    title = None
    description = None
    published = None

    def __init__(self, article_id=None, url=None, title=None, description=None, published=None):
        if article_id and url:
            self.id = article_id

        self.url = url
        self.title = title
        self.description = description
        if published:
            self.published = published
        else:
            self.published = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        if article_id and not url:
            res = DB.select('articles', where="id=$article_id", vars={'article_id': article_id})
            if res:
                a = res[0]
                self.id = a.id
                self.url = a.url
                self.title = a.title
                self.description = a.description
            else:
                raise ArticleException("Can't load article with id=%s" % article_id)

    def save(self):
        if self.id:
            DB.update(
                'articles',
                where="id=$id",
                vars={'id': self.id},
                url=self.url,
                title=self.title,
                description=self.description,
                published=self.published
            )
        else:
            self.id = DB.insert(
                'articles',
                url=self.url,
                title=self.title,
                description=self.description,
                published=self.published
            )
        return self.id

    def get_urls_from_description(self):
        return []


class UserArticle:
    id = None
    user_id = None
    article_id = None
    source_count = None
    is_read = None
    is_liked = None

    def __init__(self, user_article_id=None, user_id=None, article_id=None):
        if user_article_id:
            self.id = user_article_id
            self._load_attrs()
        elif user_id and article_id:
            res = DB.select('user_articles',
                            where="user_id=$user_id AND article_id=$article_id",
                            vars={'user_id': user_id, 'article_id': article_id})
            if res:
                self._set_attrs(res[0])
            else:
                self.id = DB.insert('user_articles', user_id=user_id, article_id=article_id)
                self._load_attrs()
        else:
            raise ArticleException("Can't create UserArticle without attributes")

    def __getattr__(self, name):
        if name == 'article':
            self._load_article()
        return getattr(self, name)

    def _set_attrs(self, row):
        if not self.id:
            self.id = row.id
        self.user_id = row.user_id
        self.article_id = row.article_id
        self.source_count = row.source_count
        self.is_read = row.is_read
        self.is_liked = row.is_liked

    def _load_attrs(self):
        res = DB.select('user_articles', where="id=$user_article_id", vars={'user_article_id': self.id})
        if res:
            self._set_attrs(res[0])
        else:
            raise ArticleException("Can't load UserArticle with id=%s" % self.id)

    def _load_article(self):
        if not self.article_id:
            raise ArticleException("Add article_id before load")
        self.article = Article(self.article_id)

    def add_location(self, location_type, location):
        return DB.insert(
            'articles_locations',
            user_article_id=self.id,
            location_type=location_type,
            location=location
        )

    def inc_source_count(self):
        return DB.update(
            'user_articles',
            where="id=$user_article_id",
            vars={
                'user_article_id': self.id
            },
            source_count=web.db.SQLLiteral('source_count+1')
        )

    def get_source_id(self):
        sql = """
                SELECT al.location source_id FROM articles_locations al
                JOIN user_articles ua ON al.user_article_id=ua.id AND user_id=$user_id
                WHERE ua.article_id = $article_id AND al.location_type='source'
            """
        res = DB.query(sql, vars={'article_id': self.article_id, 'user_id': self.user_id})
        if res:
            return res[0]['source_id']
        return False

    def read(self):
        if self.id and not self.is_read:
            self.is_read = 1
            DB.update(
                'user_articles',
                where="id=$id",
                vars={'id': self.id},
                is_read=self.is_read,
                read_time=web.db.SQLLiteral('NOW()')
            )
            source_id = self.get_source_id()
            if source_id:
                mSource().increase_read_count(source_id, self.user_id)
        else:
            return False
        return True

    def like(self, is_liked=1):
        if self.id:
            self.is_liked = is_liked
            DB.update(
                'user_articles',
                where="id=$id",
                vars={'id': self.id},
                is_liked=self.is_liked,
                like_time=web.db.SQLLiteral('NOW()')
            )
            source_id = self.get_source_id()
            if source_id:
                mSource().increase_like_count(source_id, self.user_id)
        else:
            return False
        return True

    def dislike(self):
        return self.like(is_liked=0)


class ArticleFactory:
    items_per_page = config.items_per_page

    def _get_by_id(self, article_id):
        return DB.select('articles', where="id=$article_id", vars={'article_id': article_id})[0]

    def _get_by_url(self, url, user_id=None):
        if not user_id:
            return DB.select('articles', where="url=$url", vars={'url': url}, limit=1)
        else:
            sql = """
                SELECT a.id, a.title, ua.user_id FROM articles a
                LEFT JOIN user_articles ua ON a.id=ua.article_id AND ua.user_id=$user_id
                WHERE a.url = $url
            """
            return DB.query(
                sql,
                vars={'user_id': user_id, 'url': url}
            )

    def _get_obj_by_url(self, url, user_id=None):
        res = self._get_by_url(url, user_id)
        if res:
            a = res[0]
            article = Article(a.id, a.url, a.title, a.description)
            return article
        return False

    def list(self, mode, page, user_id):
        page = int(page)
        offset = self.items_per_page * (page - 1)
        items = []
        count = 0
        if mode == 'all':
            sql = """
                SELECT a.*, ua.is_liked, ua.is_read, ua.source_count FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL
                ORDER BY a.id DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(a.id) cnt FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL
            """
            items = DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': self.items_per_page,
                    'offset': offset}
            )
            #count = DB.query(sql_count, vars={'user_id': user_id})[0]['cnt']
        if mode == 'unread':
            offset = config.unread_items_per_page * (page - 1)
            sql = """
                SELECT a.*, ua.is_liked, ua.is_read, ua.source_count FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL AND ua.is_read = 0
                ORDER BY a.published DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(a.id) cnt FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL AND ua.is_read = 0
            """
            items = DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': config.unread_items_per_page,
                    'offset': offset}
            )
            count = DB.query(sql_count, vars={'user_id': user_id})[0]['cnt']
        if mode == 'read':
            sql = """
                SELECT a.*, ua.is_liked, ua.is_read, ua.source_count FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL AND ua.is_read = 1
                ORDER BY ua.read_time DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(a.id) cnt FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL AND ua.is_read = 1
            """
            items = DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': self.items_per_page,
                    'offset': offset}
            )
            count = DB.query(sql_count, vars={'user_id': user_id})[0]['cnt']
        if mode == 'liked':
            sql = """
                SELECT a.*, ua.is_liked, ua.is_read, ua.source_count FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL AND ua.is_liked = 1
                ORDER BY ua.like_time DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(a.id) cnt FROM articles a
                JOIN user_articles ua ON a.id=ua.article_id
                WHERE ua.user_id=$user_id AND a.title IS NOT NULL AND ua.is_liked=1
            """
            items = DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': self.items_per_page,
                    'offset': offset}
            )
            count = DB.query(sql_count, vars={'user_id': user_id})[0]['cnt']
        return items, int(math.ceil(count / float(self.items_per_page)))

    def add(self, url, user_id=None, location_type=None, location=None):
        art = self._get_obj_by_url(url, user_id)
        if art:
            article_id = art.id
            if not art.title:
                create_job(config.que_download_article, str(article_id))
            if user_id and not art.user_id:
                self.add_article_to_user(article_id, user_id, location_type, location)
        else:
            article_id = DB.insert('articles', url=url)
            create_job(config.que_download_article, str(article_id))
        return article_id

    def add_article_to_user(self, article_id, user_id, location_type=None, location=None):
        ua = UserArticle(user_id=user_id, article_id=article_id)
        if location_type and location:
            ua.add_location(location_type, location)
        return True
