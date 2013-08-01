#!/usr/bin/env python
# coding: utf-8
import os
import sys
import pymorphy2
import re
import web

web.config.debug = False

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import config
from models.article import Article
from models.user import get_users
from models.classifier import FisherClassifier
from word_lists import excluded_words

DB = config.DB


def _is_good_words(word):
    if word in excluded_words:
        return False
    if len(word) < 5 or len(word) > 13:
        return False

    num = re.compile('\\d+')
    if num.match(word):
        return False

    return True


def get_words(doc):
    # Split the words by non-alpha characters
    splitter = re.compile('\\W*', re.UNICODE)
    words = []
    ma = pymorphy2.MorphAnalyzer()
    for w in splitter.split(doc):
        if len(w) < 5 or len(w) > 13:
            continue
        w = w.lower().replace('_', '')

        if _is_good_words(w.lower()):
            res = ma.parse(w)
            if res:
                words.append(res[0].normal_form)

    # Return the unique set of words only
    result = dict([(w, 1) for w in words])
    #print_word_array(sorted(result))
    return sorted(result)


def desroy_classifier_data():
    DB.query("TRUNCATE cc;")
    DB.query("TRUNCATE fc;")
    DB.query("UPDATE user_articles SET is_handled=0;")


def set_article_handled(ua_id):
    return DB.update(
        'user_articles',
        where="id=$id",
        vars={'id': ua_id},
        is_handled=1
    )


def handle_articles(cl, user_id):
    categories = {
        'good': 1,
        'bad':  2
    }
    for cat in categories:
        sql = """
            SELECT ua.id, a.description FROM articles a
            JOIN user_articles ua ON a.id=ua.article_id
            WHERE ua.is_liked=$is_liked AND ua.user_id=$user_id AND is_handled=0
            LIMIT 2
        """
        articles = DB.query(
            sql,
            vars={'user_id': user_id, 'is_liked': categories[cat]}
        )
        for ua in articles:
            cl.train(ua.description, cat, user_id)
            print 'Handle UserArticle: %s' % ua.id
            set_article_handled(ua.id)

    return True


def run_training(cl):
    for user in get_users():
        print 'Handle articles for user: %s' % user.name
        handle_articles(cl, user.id)
    return True


cl = FisherClassifier(get_words)
#desroy_classifier_data()
run_training(cl)
