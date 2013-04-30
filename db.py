import config
import datetime
import feedparser
import math
import time

import cl

from mq import create_job


class mSource:
    def list(self, user_id=1):
        sql = """
                SELECT s.*, us.is_active  FROM sources s
                JOIN user_sources us ON s.id=us.source_id AND us.user_id=$user_id
            """
        items = config.DB.query(
            sql,
            vars={
                'user_id': user_id,
            }
        )
        return items

    def add(self, s_type, url, title):
        res = False
        if s_type == 'feed':
            res = feedparser.parse(url)
            if res:
                if not title:
                    title = res.feed.title
                res = config.DB.insert('sources', type=s_type, url=url, title=title)
        elif s_type == 'twitter':
            res = config.DB.insert('sources', type=s_type, url=url, title=url)
        return res

    def add_to_user(self, user_id, s_type, url, title):
        source_id = self.add(s_type, url, title)
        if source_id:
            config.DB.insert('user_sources', user_id=user_id, source_id=source_id)
        return True

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


class mService:
    def load_news(self):
        rows = config.DB.select('sources', where="NOW() - INTERVAL 1 HOUR > last_update OR last_update is NULL")
        for source in rows:
                print source.title
                create_job('sources_for_update', str(source.id))
