# coding: utf-8
import json

import web

import config
from models.source import SourceFactory, UserSource
from models.article import ArticleFactory, UserArticle
from models.user import login
from models.service import save_opml


t_globals = dict(
    datestr=web.datestr,
    str=str,
    sort=sorted,
    ctx=web.web_session
)
render = web.template.render('templates/', cache=config.cache, globals=t_globals)
render._keywords['globals']['render'] = render

SOURCE_LIST_URL = '/source/list'
HOME_SCREEN = '/article/list/unread/1'


def get_user():
    user_id = web.web_session.user_id
    if not user_id:
        raise web.seeother('/login')
    return user_id


class Index:
    def GET(self):
        return render.base()


class SourceList:
    def list(self):
        user_id = get_user()
        s = SourceFactory()
        l = s.list(user_id)
        return render.source.list(l)

    def GET(self):
        return render.app(self.list())


class SourceAdd:
    def GET(self):
        data = web.input()
        url = data.u
        title = data.t or 'No title'
        username = data.l
        if not url:
            return False
        res = login(username)
        if not res:
            return json.dumps({'success': False})
        user_id = res['id']

        sf = SourceFactory()
        sf.add_to_user(user_id, 'feed', url, title, config.default_source_category)

        js = """
        var d = document;
        d.title = d.title.replace(/\(Saving...\) /g, '');
        """
        web.header('Content-type', 'text/javascript')
        return js

    def POST(self):
        user_id = get_user()
        data = web.input()
        url = data.addSourceUrl
        title = data.addSourceTitle or 'No title'
        s_type = data.addSourceType
        sf = SourceFactory()
        sf.add_to_user(user_id, s_type, url, title, config.default_source_category)
        raise web.seeother(SOURCE_LIST_URL)


class SourceEdit:
    def get_form(self, source_id, user_id):
        form = web.form
        us = UserSource(source_id, user_id)
        return form.Form(
            form.Hidden("source_id", value=source_id),
            form.Textbox("url", value=us.source.url, description="URL"),
            form.Textbox("title", value=us.title, description="Title"),
            form.Textbox("category", value=us.category, description="Category"),
            form.Button("submit", type="submit", description="Register")
        )()

    def GET(self, source_id):
        user_id = get_user()
        return render.app(render.source.edit(self.get_form(source_id, user_id)))

    def POST(self, source_id):
        user_id = get_user()
        data = web.input()
        if 'title' in data.keys() and 'category' in data.keys():
            us = UserSource(source_id, user_id)
            us.set_title(data.title)
            us.set_category(data.category)
        return render.app(render.source.edit(self.get_form(source_id,user_id)))


class SourceDelete:
    def GET(self, source_id):
        user_id = get_user()
        s = SourceFactory()
        s.delete_user_source(int(source_id), int(user_id))
        raise web.seeother(SOURCE_LIST_URL)


class SourceDisable:
    def GET(self, user_source_id):
        get_user()
        s = UserSource(user_source_id)
        s.disable()
        raise web.seeother(SOURCE_LIST_URL)


class SourceEnable:
    def GET(self, user_source_id):
        get_user()
        s = UserSource(user_source_id)
        s.enable()
        raise web.seeother(SOURCE_LIST_URL)


class ServiceImportOpml:
    def load_window(self):
        return render.service.import_opml_form()

    def GET(self):
        return render.app(self.load_window())

    def POST(self):
        user_id = get_user()
        data = web.input()
        if 'opml' in data.keys():
            opml = data.opml
            save_opml(user_id, opml)
            return render.app('OPML saved.')

        return render.app(self.load_window())


class ArticleRead:
    def POST(self):
        user_id = get_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            return json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.read()})

    def GET(self):
        return json.dumps({'success': True})


class ArticleReadAll:
    def POST(self):
        user_id = get_user()
        data = web.input()
        try:
            article_ids = json.loads(data.article_ids)
        except ValueError:
            return json.dumps({'success': False, 'msg': 'Invalid data format'})

        if not article_ids:
            return json.dumps({'success': False})
        for article_id in article_ids:
            ua = UserArticle(user_id=user_id, article_id=article_id)
            ua.read()
        return json.dumps({'success': True})

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
        user_id = get_user()
        page = self.list(mode, page, user_id)
        return render.app(page)


class ArticleLike:
    def POST(self):
        user_id = get_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            return json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.like()})


class ArticleDislike:
    def POST(self):
        user_id = get_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            return json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.dislike()})


class ArticleAdd():
    def GET(self):
        data = web.input()
        url = data.u
        referrer = data.r
        username = data.l
        #time = data.t
        if not url:
            return False
        res = login(username)
        if not res:
            return json.dumps({'success': False})
        user_id = res['id']

        ArticleFactory().add(url, user_id, location_type='browser', location=referrer)

        js = """
        var d = document;
        d.title = d.title.replace(/\(Saving...\) /g, '');
        """
        web.header('Content-type', 'text/javascript')
        return js


class Login():
    def GET(self):
        data = web.input()
        if 'u' in data.keys():
            user = login(data.u)
            if user:
                web.web_session.user_id = user['id']
                web.web_session.username = user['name']
        else:
            web.web_session.user_id = 1
            web.web_session.username = 'Test'
        raise web.seeother(HOME_SCREEN)


class Logout():
    def GET(self):
        web.web_session.user_id = 0
        web.web_session.kill()
        raise web.seeother('/')
