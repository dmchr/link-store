#!/usr/bin/env python
import datetime
import feedparser
import os
import pika
import re
import sys
import time
import urllib2
from urlparse import urlparse

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import config
from models.article import Article, ArticleFactory, UserArticle

host = config.rabbit_host
queue = config.que_update_source
DB = config.DB
twitter_feed_url = config.twitter_feed_url

HTTP_TIMEOUT = 2


def get_domain(url):
    res = urlparse(url)
    if res.hostname:
        return res.hostname
    return False


def get_source(source_id):
    return DB.select('sources', where="id=$source_id", vars={'source_id': source_id})


def add_article_location(user_article, location_type, location):
    res = DB.select(
        'articles_locations',
        where="user_article_id=$user_article_id AND location_type=$location_type AND location=$location",
        vars={
            'user_article_id': user_article.id,
            'location_type': location_type,
            'location': location
        }
    )
    if not res:
        location_id = user_article.add_location(location_type, location)
        user_article.inc_source_count()
        return location_id
    return False


def add_article_to_users(source_id, article_id):
    items = DB.select('user_sources', where="source_id=$source_id AND is_active=1", vars={'source_id': source_id})
    for item in items:
        article = UserArticle(user_id=item.user_id, article_id=article_id)
        add_article_location(article, 'source', source_id)
    return True


def insert_article(source_id, item, content=None):
    def format_publish_time(item):
        tm = item.get('published_parsed') or item.get('updated_parsed') or time.localtime()
        return time.strftime('%Y-%m-%d %H:%M:%S', tm)

    article = Article()
    article.title = item.get('title', 'No title')
    article.url = item.link
    if not content:
        content = item.get('description', 'No description')
    article.description = content
    article.published = format_publish_time(item)
    article.save()

    add_article_to_users(source_id, article.id)
    return article.id


def save_urls(parent_article_id, source_id, urls):
    if not urls:
        return False
    for url in urls:
        print 'Save url: %s' % url
        article_id = ArticleFactory().add(url)

        items = DB.select('user_sources', where="source_id=$source_id", vars={'source_id': source_id})
        for item in items:
            user_article = UserArticle(user_id=item.user_id, article_id=article_id)
            add_article_location(user_article, 'article', parent_article_id)


def update_feed(source):
    def get_http_response(url):
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        try:
            response = opener.open(url, None, HTTP_TIMEOUT)
        except urllib2.URLError as exc:
            print exc
            return False
        return response

    def handle_feed_item(item, source):
        link = item.link
        if 'title' in item.keys():
            title = item.title
        else:
            title = 'No title'
        existed_link = DB.select("articles", where="url=$url", vars={'url': link})
        if not existed_link:
            article_id = insert_article(source.id, item)
            print '      ', article_id, title

    response = get_http_response(source['url'])
    if not response:
        return False

    res = feedparser.parse(response)
    for item in res['entries']:
        handle_feed_item(item, source)
    return True


def update_twitter(source):
    def handle_urls(content, urls):
        urls_for_save = []
        for u in urls:
            request = urllib2.Request(u)
            opener = urllib2.build_opener()
            try:
                f = opener.open(request)
            except urllib2.URLError as exc:
                print exc
                continue
            if f.url:
                print f.url, get_domain(f.url)
                content = content.replace(u, '<a href="{0}">{0}</a>'.format(f.url))
                if get_domain(f.url) == 'twitter.com':
                    print 'Link to twitter. Continue...'
                    continue
                is_image = False
                for ext in ['jpg', 'png']:
                    if f.url.lower().find('.%s' % ext) != -1:
                        is_image = True
                        break
                if is_image:
                    print 'Link is image. Continue...'
                    continue
                urls_for_save.append(f.url)
        return content, urls_for_save

    print source.url
    url = twitter_feed_url % source.url
    res = feedparser.parse(url)

    for item in res['entries']:
        link = item.link
        content = item.title
        url_pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, content)
        if urls:
            content, urls_for_save = handle_urls(content, urls)
        existed_article = DB.select("articles", where="url=$url", vars={'url': link})
        if not existed_article:
            article_id = insert_article(source.id, item, content)
            print '      ', article_id, content
        else:
            article_id = existed_article[0].id
        if article_id == 835:
            save_urls(article_id, source.id, urls_for_save)
    return True


def update_source(source_id):
    res = get_source(source_id)
    if not res:
        return False
    source = res[0]
    if source.type == 'feed':
        update_feed(source)
    elif source.type == 'twitter':
        update_twitter(source)
    return True


def callback(ch, method, properties, body):
    print " [x] Received %r" % (body,)
    source_id = int(body)
    if update_source(source_id):
        DB.update(
            'sources',
            where="id=$source_id",
            vars={'source_id': source_id},
            last_update=datetime.datetime.now()
        )
    print " [x] Done"
    ch.basic_ack(delivery_tag=method.delivery_tag)


connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
channel = connection.channel()
channel.queue_declare(queue=queue, durable=True)
print ' [*] Waiting for messages. To exit press CTRL+C'
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue=queue)
channel.start_consuming()
