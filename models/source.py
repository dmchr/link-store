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

    def __init__(self, source_id=None, type=None, url=None, title=None):
        if source_id:
            self.id = source_id
            self._load_attrs()
        elif type and url:
            sources = DB.select('sources', where='url=$url', vars={'url': url})
            if sources:
                self._set_attrs(sources[0])
            else:
                source_id = self._insert(type, url, title)
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

    def _insert(self, type, url, title):
        if type == 'feed':
            parse_result = feedparser.parse(url)
            if parse_result:
                if not title:
                    title = parse_result.feed.title
                return DB.insert('sources', type=type, url=url, title=title)
        elif type == 'twitter':
            return DB.insert('sources', type=type, url=url, title=url)
        return False


class UserSource:
    id = None
    user_id = None
    source_id = None
    is_active = None
    read_count = None
    like_count = None
    category = None

    def __init__(self, user_source_id=None, user_id=None, source_id=None, category=None):
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
                if category:
                    self.id = DB.insert('user_sources', user_id=user_id, source_id=source_id, category=category)
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
                SELECT s.*, us.is_active, us.read_count, us.like_count, us.category
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

    def add_to_user(self, user_id, s_type, url, title=None, category=None):
        source = Source(type=s_type, url=url, title=title)
        if source.id:
            user_source = UserSource(user_id=user_id, source_id=source.id, category=category)
        if user_source.id:
            return user_source.id
        return False

    def delete(self, sid):
        if sid and type(sid) == int:
            DB.delete('sources', where="id=$id", vars={'id': sid})
        return True

    def disable(self, sid, user_id):
        if sid and type(sid) == int:
            DB.update(
                'user_sources',
                where="source_id=$source_id AND user_id=$user_id",
                vars={'source_id': sid, 'user_id': user_id},
                is_active=0
            )
        return True

    def enable(self, sid, user_id):
        if sid and type(sid) == int:
            DB.update(
                'user_sources',
                where="source_id=$source_id AND user_id=$user_id",
                vars={'source_id': sid, 'user_id': user_id},
                is_active=1
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

    def increase_like_count(self, source_id, user_id):
        return DB.update(
            'user_sources',
            where="source_id=$source_id AND user_id=$user_id",
            vars={
                'user_id': user_id,
                'source_id': source_id
            },
            like_count=web.db.SQLLiteral('like_count+1')
        )

    def load_news(self):
        rows = DB.select('sources', where="NOW() - INTERVAL 1 HOUR > last_update OR last_update is NULL", limit=500)
        for source in rows:
            print source.title
            create_job('sources_for_update', str(source.id))