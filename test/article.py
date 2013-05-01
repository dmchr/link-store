import unittest
from models import article

test_url = 'http://yandex.ru'


class TestArticle(unittest.TestCase):

    def test_init(self):
        a = article.Article()
        self.assertIsNone(a.id)
        a.url = test_url
        a.save()
        self.assertIsInstance(a.id, long)
