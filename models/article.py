import config
import math
import web
from mq import create_job

DB = config.DB


class ArticleException(Exception):
    pass


class Article:
    id = None
    url = None
    title = None
    description = None

    def __init__(self, article_id=None, url=None, title=None, description=None):
        if article_id and url:
            self.id = article_id

        self.url = url
        self.title = title
        self.description = description

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
                description=self.description
            )
        else:
            self.id = DB.insert('articles', url=self.url, title=self.title, description=self.description)
        return True

    def get_urls_from_description(self):
        return []


class UserArticle:
    id = None
    user_id = None
    article_id = None
    source_count = None

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
                SELECT n.*, l.is_liked, ua.source_count FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                LEFT JOIN user_likes l ON n.id=l.article_id
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL
                ORDER BY n.id DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL
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
                SELECT n.*, l.is_liked, ua.source_count FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                LEFT JOIN user_reads r ON n.id=r.article_id
                LEFT JOIN user_likes l ON n.id=l.article_id
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL AND r.id IS NULL
                ORDER BY n.published DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                LEFT JOIN user_reads r ON n.id=r.article_id
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL AND r.id IS NULL
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
                SELECT n.*, l.is_liked, ua.source_count FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_reads r ON n.id=r.article_id
                LEFT JOIN user_likes l ON n.id=l.article_id
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL
                ORDER BY r.created DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_reads r ON n.id=r.article_id
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL
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
                SELECT n.*, l.is_liked, ua.source_count FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_likes l ON n.id=l.article_id AND l.is_liked=1
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL
                ORDER BY l.created DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_likes l ON n.id=l.article_id AND l.is_liked=1
                WHERE ua.user_id=$user_id AND n.title IS NOT NULL
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

    def read(self, article_id, user_id):
        read_news = DB.select('user_reads',
                              where="user_id=$user_id AND article_id=$article_id",
                              vars={
                                  'user_id': int(user_id),
                                  'article_id': int(article_id)
                              })
        if read_news:
            return False
        inserted_id = DB.insert('user_reads', user_id=user_id, article_id=article_id)
        sql = """
            SELECT al.location source_id FROM articles_locations al
            JOIN user_articles ua ON al.user_article_id=ua.id AND user_id=$user_id
            WHERE ua.article_id = $article_id AND al.location_type='source'
        """
        res = DB.query(sql, vars={'article_id': article_id, 'user_id': int(user_id)})
        if res:
            source_id = res[0]['source_id']
            DB.update(
                'user_sources',
                where="source_id=$source_id AND user_id=$user_id",
                vars={
                    'user_id': int(user_id),
                    'source_id': int(source_id)
                },
                read_count=web.db.SQLLiteral('read_count+1')
            )
        return inserted_id

    def like(self, article_id, user_id, is_liked=1):
        liked_news = DB.select('user_likes',
                               where="user_id=$user_id AND article_id=$article_id",
                               vars={
                                   'user_id': int(user_id),
                                   'article_id': int(article_id)
                               })
        if not liked_news:
            inserted_id = DB.insert('user_likes', user_id=user_id, article_id=article_id, is_liked=is_liked)
        else:
            like_mark = liked_news[0]['is_liked']
            if like_mark != is_liked:
                DB.update(
                    'user_likes',
                    where="user_id=$user_id AND article_id=$article_id",
                    vars={
                        'user_id': int(user_id),
                        'article_id': int(article_id)
                    },
                    is_liked=is_liked
                )
        return True

    def dislike(self, article_id, user_id):
        return self.like(article_id, user_id, 0)

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
