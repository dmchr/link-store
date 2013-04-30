#!/usr/bin/env python
import datetime
import feedparser
import pika
import re
import time
import web
import urllib2
from urlparse import urlparse

queue = 'sources_for_update'
DB = web.database(dbn='mysql', db='news', user='sot', pw='sot')


def get_domain(url):
    res = urlparse(url)
    if res.hostname:
        return res.hostname
    return False


def get_source(source_id):
    return DB.select('sources', where="id=$source_id", vars={'source_id': source_id})[0]


def add_article_location(user_article_id, location_type, location):
    return DB.insert('articles_locations', user_article_id=user_article_id, location_type=location_type, location=location)


def add_article_to_users(source_id, article_id):
    items = DB.select('user_sources', where="source_id=$source_id", vars={'source_id': source_id})
    for item in items:
        user_article_id = DB.insert('user_articles', user_id=item.user_id, article_id=article_id)
        add_article_location(user_article_id, 'source', source_id)
    return True


def insert_article(source_id, item, content=None):
    title = item.get('title', 'No title')
    link = item.link
    if not content:
        content = item.get('description', 'No description')
    tm = item.get('published_parsed') or item.get('updated_parsed') or time.localtime()
    published = time.strftime('%Y-%m-%d %H:%M:%S', tm)
    article_id = DB.insert('articles', url=link, title=title, description=content, published=published)
    add_article_to_users(source_id, article_id)
    return article_id


#def save_url(url):


def update_feed(source):
    res = feedparser.parse(source['url'])
    for item in res['entries']:
        link = item.link
        title = item.title
        existed_link = DB.select("articles", where="url=$url", vars={'url': link})
        if not existed_link:
            article_id = insert_article(source.id, item)
            print '      ', article_id, title
    return True


def update_twitter(source):
    print source.url
    url = 'http://api.twitter.com/1/statuses/user_timeline.rss?screen_name=%s' % source.url
    res = feedparser.parse(url)

    for item in res['entries']:
        link = item.link
        content = item.title
        print content
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        print urls
        if urls:
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
                    print 'Save url'
            print content
        existed_link = DB.select("articles", where="url=$url", vars={'url': link})
        if not existed_link:
            article_id = insert_article(source.id, item, content)
            print '      ', article_id, content
    return True


def update_source(source_id):
    source = get_source(source_id)
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

#update_source(33)


connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue=queue, durable=True)
print ' [*] Waiting for messages. To exit press CTRL+C'
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue=queue)
channel.start_consuming()
