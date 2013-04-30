import web

urls = (
    '/', 'views.view.Index',
    '/source/list', 'views.view.SourceList',
    '/source/add', 'views.view.SourceAdd',
    '/source/delete/(\d+)', 'views.view.SourceDelete',
    '/source/enable/(\d+)', 'views.view.SourceEnable',
    '/source/disable/(\d+)', 'views.view.SourceDisable',
    '/service/load-news', 'views.view.ServiceLoadNews',
    '/article/list/(.+)/(\d+)', 'views.view.ArticleList',
    '/a/add', 'views.view.ArticleAdd',
    '/a/read', 'views.view.ArticleRead',
    '/a/like', 'views.view.ArticleLike',
    '/a/dislike', 'views.view.ArticleDislike',
    '/login', 'views.view.Login',
    '/logout', 'views.view.Logout'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.internalerror = web.debugerror

    session = web.session.Session(
        app,
        web.session.DiskStore('sessions'),
        initializer={'user_id': 0, 'username': 'Guest'}
    )
    web.web_session = session

    app.run()
