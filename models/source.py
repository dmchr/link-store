# coding: utf-8
import config
import feedparser
import web

from mq import create_job

DB = config.DB


class SourceException(Exception):
    pass


class Source:
    id = None
    type = None
    url = None
    title = None
    last_update = None

    def __init__(self, source_id=None, type=None, url=None):
        if source_id:
            self.id = source_id
            self._load_attrs()
        elif type and url:
            sources = DB.select('sources', where='url=$url', vars={'url': url})
            if sources:
                self._set_attrs(sources[0])
            else:
                source_id = self._insert(type, url)
                if source_id:
                    self.id = source_id
                    self._load_attrs()
                else:
                    raise SourceException('Unable to add source')

    def _set_attrs(self, item):
        self.id = item.id
        self.type = item.type
        self.url = item.url
        self.title = item.title
        self.last_update = item.last_update

    def _load_attrs(self):
        if not self.id:
            raise SourceException("Can't load source without id")

        res = DB.select('sources', where="id=$source_id", vars={'source_id': self.id})
        if res:
            self._set_attrs(res[0])
        else:
            raise SourceException("Can't load source with id=%s" % self.id)

    def _insert(self, type, url):
        if type == 'feed':
            parse_result = feedparser.parse(url)
            if parse_result:
                title = parse_result.feed.title
                return DB.insert('sources', type=type, url=url, title=title)
        elif type == 'twitter':
            return DB.insert('sources', type=type, url=url, title=url)
        return False


class UserSource:
    id = None
    user_id = None
    source_id = None
    title = None
    is_active = None
    read_count = None
    like_count = None
    category = None

    def __init__(self, user_source_id=None, user_id=None, source_id=None, title=None, category=None):
        if user_source_id:
            self.id = user_source_id
            self._load_attrs()
        elif user_id and source_id:
            res = DB.select('user_sources',
                            where="user_id=$user_id AND source_id=$source_id",
                            vars={'user_id': user_id, 'source_id': source_id})
            if res:
                self._set_attrs(res[0])
            else:
                if category and title:
                    self.id = DB.insert(
                        'user_sources',
                        user_id=user_id,
                        source_id=source_id,
                        title=title,
                        category=category
                    )
                elif category or title:
                    if category:
                        self.id = DB.insert('user_sources', user_id=user_id, source_id=source_id, category=category)
                    else:
                        self.id = DB.insert('user_sources', user_id=user_id, source_id=source_id, title=title)
                else:
                    self.id = DB.insert('user_sources', user_id=user_id, source_id=source_id)
                self._load_attrs()
        else:
            raise SourceException("Can't create UserSource without attributes")

    def __getattr__(self, name):
        if name == 'source':
            self._load_source()
        return getattr(self, name)

    def _set_attrs(self, row):
        if not self.id:
            self.id = row.id
        self.user_id = row.user_id
        self.source_id = row.source_id
        self.title = row.title
        self.is_active = row.is_active
        self.read_count = row.read_count
        self.like_count = row.like_count
        self.category = row.category

    def _load_attrs(self):
        res = DB.select('user_sources', where="id=$user_source_id", vars={'user_source_id': self.id})
        if res:
            self._set_attrs(res[0])
        else:
            raise SourceException("Can't load UserSource with id=%s" % self.id)

    def _load_source(self):
        if not self.source_id:
            raise SourceException("Add source_id before load")
        self.source = Source(self.source_id)

    def set_title(self, title):
        """
        Изменить название фида пользователя
        :type title: str
        :rtype: int
        """
        if not title:
            return False
        self.title = title
        return DB.update(
            'user_sources',
            where="id=$id",
            vars={'id': self.id},
            title=self.title
        )

    def set_category(self, category):
        """
        Изменить категорию фида пользователя
        :type category: str
        :rtype: int
        """
        if not category:
            return False
        self.category = category
        return DB.update(
            'user_sources',
            where="id=$id",
            vars={'id': self.id},
            category=self.category
        )

    def enable(self, is_active=1):
        self.is_active = is_active
        DB.update(
            'user_sources',
            where="id=$id",
            vars={'id': self.id},
            is_active=self.is_active
        )
        return True

    def disable(self):
        return self.enable(is_active=0)


class SourceFactory:
    def list(self, user_id=0):
        def prepare_items(items):
            res = {}
            for item in items:
                category = item['category']
                if category not in res:
                    res[category] = []
                res[category].append(item)
            return res

        sql = """
            SELECT s.type, s.url, us.id, us.title, us.is_active, us.read_count, us.like_count, us.category
            FROM user_sources us #FORCE INDEX (`idx-users_sources-user_id`)
            JOIN sources s ON us.source_id=s.id
            WHERE us.user_id=$user_id
            ORDER BY us.is_active DESC, us.like_count DESC, us.read_count DESC
        """
        items = DB.query(
            sql,
            vars={
                'user_id': user_id,
            }
        )
        return prepare_items(items)

    def add_to_user(self, user_id, source_type, url, title=None, category=None):
        source = Source(type=source_type, url=url)
        if source.id:
            user_source = UserSource(user_id=user_id, source_id=source.id, title=title, category=category)
        if user_source.id:
            return user_source.id
        return False

    def delete_source(self, source_id):
        if source_id and type(source_id) == int:
            DB.delete('sources', where="id=$id", vars={'id': source_id})
        return True

    def delete_user_source(self, source_id, user_id):
        print source_id, type(source_id), user_id, type(user_id)
        if not source_id or type(source_id) != int or not user_id or type(user_id) != int:
            return False
        DB.delete(
            'user_sources',
            where="source_id=$source_id AND user_id=$user_id",
            vars={
                'source_id': source_id,
                'user_id': user_id
            }
        )
        return True

    def increase_read_count(self, source_id, user_id):
        return DB.update(
            'user_sources',
            where="source_id=$source_id AND user_id=$user_id",
            vars={
                'user_id': user_id,
                'source_id': source_id
            },
            read_count=web.db.SQLLiteral('read_count+1')
        )

    def change_like_count(self, source_id, user_id, literal):
        return DB.update(
            'user_sources',
            where="source_id=$source_id AND user_id=$user_id",
            vars={
                'user_id': user_id,
                'source_id': source_id
            },
            like_count=web.db.SQLLiteral(literal)
        )

    def increase_like_count(self, source_id, user_id):
        return self.change_like_count(source_id, user_id, 'like_count+1')

    def decrease_like_count(self, source_id, user_id):
        return self.change_like_count(source_id, user_id, 'like_count-1')

    def load_news(self):
        rows = DB.select('sources', where="NOW() - INTERVAL 1 HOUR > last_update OR last_update is NULL", limit=500)
        for source in rows:
            create_job('sources_for_update', str(source.id))