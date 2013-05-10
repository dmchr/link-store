import unittest
from config import DB
from models import article

test_url1 = 'http://yandex.ru'
test_url2 = 'http://google.com'
wrong_id = -1
user_id = 1


class TestArticle(unittest.TestCase):
    a = None

    def setUp(self):
        DB.delete('articles', where='1=1')
        self.a = article.Article()
        self.a.url = test_url1
        self.a.title = 'Test title'
        self.a.description = 'Test description'
        self.a.save()

    def test_init_create_article(self):
        a = article.Article()
        a.url = test_url1
        a.save()
        self.assertIsInstance(a.id, long)

        b = article.Article(url=test_url1, title='Title', description='Description')
        b.save()
        self.assertIsInstance(b.id, long)

    def test_init_load_article(self):
        b = article.Article(self.a.id)
        self.assertEqual(self.a.url, b.url)
        b.url = test_url2
        b.save()

        c = article.Article(self.a.id)
        self.assertNotEqual(self.a.url, c.url)

    def test_init_load_article_with_wrong_id(self):
        with self.assertRaises(article.ArticleException):
            article.Article(wrong_id)


class TestUserArticle(unittest.TestCase):
    a = None
    ua = None

    def setUp(self):
        DB.delete('user_articles', where='1=1')
        DB.delete('users', where='1=1')
        self.a = article.Article()
        self.a.url = test_url1
        self.a.title = 'Test title'
        self.a.description = 'Test description'
        self.a.save()

        DB.insert('users', id=user_id, name='Guest')
        self.ua = article.UserArticle(user_id=user_id, article_id=self.a.id)

    def test_init_load_user_article_by_id(self):
        b = article.UserArticle(self.ua.id)
        self.assertEqual(self.ua.user_id, b.user_id)

    def test_init_create_user_article_by_user_and_article(self):
        b = article.UserArticle(user_id=user_id, article_id=self.a.id)
        self.assertIsInstance(b.id, long)

    def test_init_create_user_article_without_attributes(self):
        with self.assertRaises(article.ArticleException):
            article.UserArticle()

    def test_init_load_user_article_with_wrong_id(self):
        with self.assertRaises(article.ArticleException):
            article.UserArticle(wrong_id)

    def test_load_article(self):
        self.assertEqual(self.a.id, self.ua.article.id)


class TestArticleFactory(unittest.TestCase):
    a = None

    def setUp(self):
        DB.delete('user_articles', where='1=1')
        DB.delete('users', where='1=1')
        self.a = article.Article()
        self.a.url = test_url1
        self.a.title = 'Test title'
        self.a.description = 'Test description'
        self.a.save()

        DB.insert('users', id=user_id, name='Guest')

    def test_add_article_to_user(self):
        res = article.ArticleFactory().add_article_to_user(self.a.id, user_id)
        self.assertTrue(res)

    def test_add_article_with_url_only(self):
        res = article.ArticleFactory()
