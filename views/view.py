import config
import json
import web

import db
from models.article import mArticle

t_globals = dict(
    datestr=web.datestr,
    str=str,
    ctx=web.web_session
)
render = web.template.render('templates/', cache=config.cache, globals=t_globals)
render._keywords['globals']['render'] = render

user_id = 1


class vSource():
    def list(self, **k):
        s = db.mSource()
        l = s.list(**k)
        return render.source.list(l)

    def add(self, form):
        return render.add_source(form)


class vArticle():
    def list(self, mode, page, user_id):
        page = int(page)
        n = mArticle()
        lst, count = n.list(mode, page, user_id)
        return render.index.list(lst, page, count)


class Index:
    def GET(self):
        return render.base()


class SourceList:
    def GET(self):
        s = vSource()
        return render.app(s.list())


class SourceAdd:
    def GET(self):
        raise web.seeother('/sources')

    def POST(self):
        data = web.input()
        url = data.addSourceUrl
        title = data.addSourceTitle or ''
        s_type = data.addSourceType
        s = db.mSource()
        s.add_to_user(user_id, s_type, url, title)
        raise web.seeother('/sources')


class SourceDelete:
    def GET(self, source_id):
        s = db.mSource()
        s.delete(int(source_id))
        raise web.seeother('/sources')


class SourceDisable:
    def GET(self, source_id):
        s = db.mSource()
        s.disable(int(source_id), user_id)
        raise web.seeother('/sources')


class SourceEnable:
    def GET(self, source_id):
        s = db.mSource()
        s.enable(int(source_id), user_id)
        raise web.seeother('/sources')


class ServiceLoadNews:
    def GET(self):
        s = db.mService()
        s.load_news()
        raise web.seeother('/')


class ArticleRead:
    def POST(self):
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        n = mArticle()
        n.read(article_id, user_id)
        return json.dumps({'success': True})

    def GET(self):
        return json.dumps({'success': True})


class ArticleList:
    def GET(self, mode, page):
        page = vArticle().list(mode, page, user_id)
        return render.app(page)


class ArticleLike:
    def POST(self):
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        n = mArticle()
        n.like(article_id, user_id)
        return json.dumps({'success': True})


class ArticleDislike:
    def POST(self):
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        n = mArticle()
        n.dislike(article_id, user_id)
        return json.dumps({'success': True})


class ArticleAdd():
    def GET(self):
        data = web.input()
        url = data.u
        referrer = data.r
        #time = data.t
        if not url:
            return False

        art_id = mArticle().add(user_id, url, referrer)
        return 'OK!!!'


class Exit():
    def GET(self):
        exit()
