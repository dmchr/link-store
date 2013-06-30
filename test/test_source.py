import unittest
from config import DB
from models import source

test_url1 = './rss/akry.xml'
test_url2 = './rss/unclemin.xml'
wrong_id = -1
user_id = 1


class TestSource(unittest.TestCase):
    s = None

    def setUp(self):
        DB.delete('sources', where='1=1')
        self.s = source.Source(type='feed', url=test_url1)

    def test_init_create_source(self):
        s = source.Source(type='feed', url=test_url2)
        self.assertIsInstance(s.id, long)

    def test_init_load_source(self):
        s = source.Source(self.s.id)
        self.assertEqual(s.id, self.s.id)


class TestUserSource(unittest.TestCase):
    s = None
    us = None

    def setUp(self):
        DB.delete('user_articles', where='1=1')
        DB.delete('user_sources', where='1=1')
        DB.delete('sources', where='1=1')
        DB.delete('users', where='1=1')

        DB.insert('users', id=user_id, name='Guest')

        self.s = source.Source(type='feed', url=test_url1)
        self.us = source.UserSource(user_id=user_id, source_id=self.s.id)

    def test_init_create_user_source(self):
        s = source.Source(type='feed', url=test_url2)
        us = source.UserSource(user_id=user_id, source_id=s.id)
        self.assertIsInstance(us.id, long)

    def test_init_load_user_source(self):
        us = source.UserSource(self.us.id)
        self.assertEqual(us.id, self.us.id)
