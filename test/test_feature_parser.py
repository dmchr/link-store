# coding: utf-8

import unittest
from models.classifier import FeatureParser


class TestFeatureParser(unittest.TestCase):
    p = None

    def setUp(self):
        self.p = FeatureParser()

    def test_bad_words(self):
        bad_words = [
            u'этот',    # меньше 5 букв
            'height',   # excluded_word
            u'ОченьДлинноеСлово'
        ]

        for w in bad_words:
            self.assertFalse(self.p._is_good_words(w))

    def test_numbers(self):
        self.assertFalse(self.p._is_contains_number('NotContainsNumbers'))

        self.assertTrue(self.p._is_contains_number('123n'))
        self.assertTrue(self.p._is_contains_number('n123'))
        self.assertTrue(self.p._is_contains_number('n123n'))
        self.assertTrue(self.p._is_contains_number('123'))

    def test_parse_text(self):
        pass

    def test_get_features(self):
        pass
