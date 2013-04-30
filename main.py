import web

urls = (
    '/', 'views.view.Index',
    '/source/list', 'views.view.SourceList',
    '/source/add', 'view.SourceAdd',
    '/source/delete/(\d+)', 'view.SourceDelete',
    '/source/enable/(\d+)', 'view.SourceEnable',
    '/source/disable/(\d+)', 'view.SourceDisable',
    '/service/load-news', 'view.ServiceLoadNews',
    '/article/list/(.+)/(\d+)', 'views.view.ArticleList',
    '/a/add', 'view.ArticleAdd',
    '/a/read', 'view.ArticleRead',
    '/a/like', 'view.ArticleLike',
    '/a/dislike', 'view.ArticleDislike',
    '/exit', 'view.Exit'
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
