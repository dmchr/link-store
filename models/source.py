import config
import feedparser

from mq import create_job


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
                FROM sources s
                JOIN user_sources us ON s.id=us.source_id AND us.user_id=1
                LEFT JOIN user_source_categories usc ON s.id=usc.source_id AND usc.user_id=$user_id
                ORDER BY us.is_active DESC, s.id
            """
        items = config.DB.query(
            sql,
            vars={
                'user_id': user_id,
            }
        )
        return prepare_items(items)

    def add(self, s_type, url, title):
        res = config.DB.select('sources', where='url=$url', vars={'url': url})
        if res:
            return res[0]['id']
        if s_type == 'feed':
            res = feedparser.parse(url)
            if res:
                if not title:
                    title = res.feed.title
                res = config.DB.insert('sources', type=s_type, url=url, title=title)
        elif s_type == 'twitter':
            res = config.DB.insert('sources', type=s_type, url=url, title=url)
        return res

    def add_to_user(self, user_id, s_type, url, title, category=None):
        source_id = self.add(s_type, url, title)
        if source_id:
            res = config.DB.select(
                'user_sources',
                where='user_id=$user_id AND source_id=$source_id',
                vars={'user_id': user_id, 'source_id': source_id}
            )
            if not res:
                config.DB.insert('user_sources', user_id=user_id, source_id=source_id)
            if category:
                self.update_category(source_id, user_id, category)

        return True

    def update_category(self, source_id, user_id, category):
        res = config.DB.select(
            'user_source_categories',
            where='user_id=$user_id AND source_id=$source_id',
            vars={'user_id': user_id, 'source_id': source_id}
        )
        if res:
            item = res[0]
            if item.name != category:
                config.DB.update(
                    'user_source_categories',
                    where='id=$id',
                    vars={'id': item.id},
                    name=category
                )
        else:
            config.DB.insert('user_source_categories', user_id=user_id, source_id=source_id, name=category)

    def delete(self, sid):
        if sid and type(sid) == int:
            config.DB.delete('sources', where="id=$id", vars={'id': sid})
        return True

    def disable(self, sid, user_id):
        if sid and type(sid) == int:
            config.DB.update(
                'user_sources',
                where="source_id=$source_id AND user_id=$user_id",
                vars={'source_id': sid, 'user_id': user_id},
                is_active=0
            )
        return True

    def enable(self, sid, user_id):
        if sid and type(sid) == int:
            config.DB.update(
                'user_sources',
                where="source_id=$source_id AND user_id=$user_id",
                vars={'source_id': sid, 'user_id': user_id},
                is_active=1
            )
        return True

    def load_news(self):
        rows = config.DB.select('sources', where="NOW() - INTERVAL 1 HOUR > last_update OR last_update is NULL")
        for source in rows:
            print source.title
            create_job('sources_for_update', str(source.id))
