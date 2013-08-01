#!/usr/bin/env python
# coding: utf-8
import os
import sys
import web

web.config.debug = False

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import config
from models.user import get_users
from models.classifier import FisherClassifier, FeatureParser

DB = config.DB


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
            LIMIT 1
        """
        articles = DB.query(
            sql,
            vars={'user_id': user_id, 'is_liked': categories[cat]}
        )
        parser = FeatureParser()
        for ua in articles:
            features = parser.get_features(ua)
            cl.train(features, cat, user_id)
            print 'Handle UserArticle: %s' % ua.id
            set_article_handled(ua.id)

    return True


def run_training(cl):
    for user in get_users():
        print 'Handle articles for user: %s' % user.name
        handle_articles(cl, user.id)
    return True


cl = FisherClassifier()
#desroy_classifier_data()
run_training(cl)
