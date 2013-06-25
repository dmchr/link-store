import config
import feedparser
import web

from mq import create_job

DB = config.DB


class mSource:
    def list(self, user_id=1):
        def prepare_items(items):
            res = {}
            for item in items:
                category = item['category']
                if not category:
                    category = '(Empty)'
                if category not in res:
                    res[category] = []
                res[category].append(item)
            return res

        sql = """
                SELECT s.*, us.is_active, us.read_count, us.like_count, usc.`name` category
                FROM user_sources us #FORCE INDEX (`idx-users_sources-user_id`)
                JOIN sources s ON us.source_id=s.id
                LEFT JOIN user_source_categories usc ON s.id=usc.source_id
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

    def add(self, s_type, url, title):
        res = DB.select('sources', where='url=$url', vars={'url': url})
        if res:
            return res[0]['id']
        if s_type == 'feed':
            res = feedparser.parse(url)
            if res:
                if not title:
                    title = res.feed.title
                res = DB.insert('sources', type=s_type, url=url, title=title)
        elif s_type == 'twitter':
            res = DB.insert('sources', type=s_type, url=url, title=url)
        return res

    def add_to_user(self, user_id, s_type, url, title, category=None):
        source_id = self.add(s_type, url, title)
        if source_id:
            res = DB.select(
                'user_sources',
                where='user_id=$user_id AND source_id=$source_id',
                vars={'user_id': user_id, 'source_id': source_id}
            )
            if not res:
                DB.insert('user_sources', user_id=user_id, source_id=source_id)
            if category:
                self.update_category(source_id, user_id, category)

        return True

    def update_category(self, source_id, user_id, category):
        res = DB.select(
            'user_source_categories',
            where='user_id=$user_id AND source_id=$source_id',
            vars={'user_id': user_id, 'source_id': source_id}
        )
        if res:
            item = res[0]
            if item.name != category:
                DB.update(
                    'user_source_categories',
                    where='id=$id',
                    vars={'id': item.id},
                    name=category
                )
        else:
            DB.insert('user_source_categories', user_id=user_id, source_id=source_id, name=category)

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

    def load_news(self):
        rows = DB.select('sources', where="NOW() - INTERVAL 1 HOUR > last_update OR last_update is NULL")
        for source in rows:
            print source.title
            create_job('sources_for_update', str(source.id))
            return True
