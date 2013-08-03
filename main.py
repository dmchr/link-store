import web

urls = (
    '/', 'views.view.Index',
    '/source/list', 'views.view.SourceList',
    '/source/add', 'views.view.SourceAdd',
    '/source/edit/(\d+)', 'views.view.SourceEdit',
    '/source/delete/(\d+)', 'views.view.SourceDelete',
    '/source/enable/(\d+)', 'views.view.SourceEnable',
    '/source/disable/(\d+)', 'views.view.SourceDisable',
    '/service/import-opml', 'views.view.ServiceImportOpml',
    '/article/list/(.+)/(\d+)', 'views.view.ArticleList',
    '/s/add', 'views.view.SourceAdd',
    '/a/add', 'views.view.ArticleAdd',
    '/a/read', 'views.view.ArticleRead',
    '/a/read-all', 'views.view.ArticleReadAll',
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
