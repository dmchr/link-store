import unittest
from config import DB
from models import source

test_url1 = './rss/akry.xml'
test_url2 = './rss/unclemin.xml'
test_category = 'Test'
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

    def test_init_create_user_source_with_category(self):
        s = source.Source(type='feed', url=test_url2)
        us = source.UserSource(user_id=user_id, source_id=s.id, category=test_category)
        self.assertIsInstance(us.id, long)
        self.assertEqual(us.category, test_category)

    def test_init_load_user_source(self):
        us = source.UserSource(self.us.id)
        self.assertEqual(us.id, self.us.id)


class TestSourceFactory(unittest.TestCase):
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

    def test_add_to_user(self):
        sf = source.SourceFactory()
        user_source_id = sf.add_to_user(user_id, 'feed', test_url2, category=test_category)
        us = source.UserSource(user_source_id)
        self.assertEqual(us.user_id, user_id)
        self.assertEqual(us.source.url, test_url2)
        self.assertEqual(us.category, test_category)
