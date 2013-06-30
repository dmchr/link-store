import json

import web

import config
from models.source import mSource
from models.article import ArticleFactory, UserArticle


t_globals = dict(
    datestr=web.datestr,
    str=str,
    sort=sorted,
    ctx=web.web_session
)
render = web.template.render('templates/', cache=config.cache, globals=t_globals)
render._keywords['globals']['render'] = render

SOURCE_LIST_URL = '/source/list'


def check_user():
    user_id = web.web_session.user_id
    if not user_id:
        raise web.seeother('/login')
    return user_id


class Index:
    def GET(self):
        return render.base()


class SourceList:
    def list(self):
        user_id = check_user()
        s = mSource()
        l = s.list(user_id)
        return render.source.list(l)

    def GET(self):
        return render.app(self.list())


class SourceAdd:
    def GET(self):
        raise web.seeother(SOURCE_LIST_URL)

    def POST(self):
        user_id = check_user()
        data = web.input()
        url = data.addSourceUrl
        title = data.addSourceTitle or ''
        s_type = data.addSourceType
        s = mSource()
        s.add_to_user(user_id, s_type, url, title, config.default_source_category)
        raise web.seeother(SOURCE_LIST_URL)


class SourceDelete:
    def GET(self, source_id):
        s = mSource()
        s.delete(int(source_id))
        raise web.seeother(SOURCE_LIST_URL)


class SourceDisable:
    def GET(self, source_id):
        user_id = check_user()
        s = mSource()
        s.disable(int(source_id), user_id)
        raise web.seeother(SOURCE_LIST_URL)


class SourceEnable:
    def GET(self, source_id):
        user_id = check_user()
        s = mSource()
        s.enable(int(source_id), user_id)
        raise web.seeother(SOURCE_LIST_URL)


class ServiceLoadNews:
    def GET(self):
        s = mSource()
        s.load_news()
        raise web.seeother('/article/list/unread/1')


class ArticleRead:
    def POST(self):
        user_id = check_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.read()})

    def GET(self):
        return json.dumps({'success': True})


class ArticleList:
    def list(self, mode, page, user_id):
        page = int(page)
        n = ArticleFactory()
        lst, count = n.list(mode, page, user_id)
        paginate = True
        if mode == 'unread':
            paginate = False
        return render.article.list(lst, page, count, paginate)

    def GET(self, mode, page):
        user_id = check_user()
        page = self.list(mode, page, user_id)
        return render.app(page)


class ArticleLike:
    def POST(self):
        user_id = check_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.like()})


class ArticleDislike:
    def POST(self):
        user_id = check_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.dislike()})


class ArticleAdd():
    def GET(self):
        user_id = check_user()
        data = web.input()
        url = data.u
        referrer = data.r
        #time = data.t
        if not url:
            return False

        article_id = ArticleFactory().add(url, user_id, location_type='browser', location=referrer)
        return json.dumps({'success': True, 'article_id': article_id})


class Login():
    def GET(self):
        web.web_session.user_id = 1
        web.web_session.username = 'Test User'
        raise web.seeother('/article/list/unread/1')


class Logout():
    def GET(self):
        web.web_session.user_id = 0
        web.web_session.kill()
        raise web.seeother('/')
