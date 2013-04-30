import config
import math
import cl
from mq import create_job


class mArticle:
    items_per_page = config.items_per_page

    def _get_by_id(self, article_id):
        return config.DB.select('articles', where="id=$article_id", vars={'article_id': article_id})[0]

    def _get_by_url(self, url, user_id=None):
        if not user_id:
            return config.DB.select('articles', where="url=$url", vars={'url': url}, limit=1)
        else:
            sql = """
                SELECT a.id, a.title, ua.user_id FROM articles a
                LEFT JOIN user_articles ua ON a.id=ua.article_id AND ua.user_id=$user_id
                WHERE a.url = $url
            """
            return config.DB.query(
                sql,
                vars={'user_id': user_id, 'url': url}
            )

    def list(self, mode, page, user_id):
        page = int(page)
        offset = self.items_per_page * (page - 1)
        items = []
        count = 0
        if mode == 'all':
            sql = """
                SELECT n.*, l.is_liked, ua.sources_count FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                LEFT JOIN user_likes l ON n.id=l.article_id
                ORDER BY n.id DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
            """
            items = config.DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': self.items_per_page,
                    'offset': offset}
            )
            count = config.DB.query(sql_count)[0]['cnt']
        if mode == 'unread':
            sql = """
                SELECT n.*, l.is_liked, 'imba' source FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                LEFT JOIN user_reads r ON n.id=r.article_id
                LEFT JOIN user_likes l ON n.id=l.article_id
                WHERE ua.user_id=$user_id AND r.id IS NULL
                ORDER BY n.published DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                LEFT JOIN user_reads r ON n.id=r.article_id AND r.user_id=$user_id
                WHERE r.id IS NULL
            """
            items = config.DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': self.items_per_page,
                    'offset': offset}
            )
            count = config.DB.query(sql_count, vars={'user_id': user_id})[0]['cnt']
        if mode == 'read':
            sql = """
                SELECT n.*, l.is_liked, 'imba' source FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_reads r ON n.id=r.article_id AND r.user_id=$user_id
                LEFT JOIN user_likes l ON n.id=l.article_id
                ORDER BY r.created DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_reads r ON n.id=r.article_id AND r.user_id=$user_id
            """
            items = config.DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': self.items_per_page,
                    'offset': offset}
            )
            count = config.DB.query(sql_count, vars={'user_id': user_id})[0]['cnt']
        if mode == 'liked':
            sql = """
                SELECT n.*, l.is_liked, 'imba' source FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_likes l ON n.id=l.article_id AND l.is_liked=1
                WHERE ua.user_id=$user_id
                ORDER BY l.created DESC
                LIMIT $limit OFFSET $offset
            """
            sql_count = """
                SELECT count(n.id) cnt FROM articles n
                JOIN user_articles ua ON n.id=ua.article_id
                JOIN user_likes l ON n.id=l.article_id AND l.is_liked=1 AND l.user_id=$user_id
            """
            items = config.DB.query(
                sql,
                vars={
                    'user_id': user_id,
                    'limit': self.items_per_page,
                    'offset': offset}
            )
            count = config.DB.query(sql_count, vars={'user_id': user_id})[0]['cnt']
        return items, int(math.ceil(count / float(self.items_per_page)))

    def read(self, article_id, user_id):
        read_news = config.DB.select('user_reads',
                                     where="user_id=$user_id AND article_id=$article_id",
                                     vars={
                                         'user_id': int(user_id),
                                         'article_id': int(article_id)
                                     })
        if read_news:
            return False
        inserted_id = config.DB.insert('user_reads', user_id=user_id, article_id=article_id)
        return inserted_id

    def like(self, article_id, user_id, is_liked=1):
        liked_news = config.DB.select('user_likes',
                                      where="user_id=$user_id AND article_id=$article_id",
                                      vars={
                                          'user_id': int(user_id),
                                          'article_id': int(article_id)
                                      })
        if not liked_news:
            inserted_id = config.DB.insert('user_likes', user_id=user_id, article_id=article_id, is_liked=is_liked)
        else:
            like_mark = liked_news[0]['is_liked']
            if like_mark != is_liked:
                config.DB.update('user_likes',
                                 where="user_id=$user_id AND article_id=$article_id",
                                 vars={
                                     'user_id': int(user_id),
                                     'article_id': int(article_id)
                                 },
                                 is_liked=is_liked)

        clf = cl.NewsParser()
        item = cl.NewsItem()
        item.description = self._get_by_id(article_id)['description']
        clf.parse(item)
        return True

    def dislike(self, article_id, user_id):
        return self.like(article_id, user_id, 0)

    def add(self, user_id, url, location_type=None, localtion=None):
        art = self._get_by_url(url, user_id)
        if art:
            print 'Article exists'
            art = art[0]
            art_id = art['id']
            if not art['title']:
                print 'Title is empty - Download article'
                create_job(config.que_download_article, str(art_id))
            if not art['user_id']:
                print 'Add article to user'
                user_article_id = config.DB.insert('user_articles', user_id=user_id, article_id=art_id)
            if location_type and localtion:
                self.add_article_location(user_article_id, location_type, localtion)
        else:
            print 'Insert article'
            art_id = config.DB.insert('articles', url=url)
            create_job('articles_for_downloads', str(art_id))
        return art_id

    def add_article_location(self, user_article_id, location_type, location):
        return config.DB.insert(
            'articles_locations',
            user_article_id=user_article_id,
            location_type=location_type,
            location=location
        )
