#!/usr/bin/env python
import os
import pika
import sys
import urllib
from readability.readability import Document
from urlparse import urlparse
from bs4 import BeautifulSoup

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import config

host = config.rabbit_host
queue = config.que_download_article
DB = config.DB


def get_url(art_id):
    res = DB.select('articles', where="id=$article_id", vars={'article_id': art_id})
    if res:
        return res[0]['url']
    return False


def get_domain(url):
    res = urlparse(url)
    if res.hostname:
        return res.hostname
    return False


def fix_url(url, domain):
    return 'http://%s%s' % (domain, url)


def update_image_paths(html, domain):
    soup = BeautifulSoup(html)
    res = soup.find_all('img')
    for r in res:
        if r.get('src')[:1] == '/':
            full_img_url = fix_url(r.get('src'), domain)
            html = html.replace(r.get('src'), full_img_url)
    return html


def download_article(url):
    print '     Download article: %s' % url
    html = urllib.urlopen(url).read()
    readable_article = Document(html).summary()
    readable_title = Document(html).short_title()
    domain = get_domain(url)

    return readable_title, update_image_paths(readable_article, domain)


def insert_article(art_id, title, article):
    print '     Update article: ', art_id, title
    DB.update(
        'articles',
        where="id=$id",
        vars={'id': int(art_id)},
        title=title,
        description=article
    )
    return True


def callback(ch, method, properties, body):
    print " [x] Received %r" % (body,)
    art_id = int(body)
    url = get_url(art_id)
    if url:
        title, article = download_article(url)
        insert_article(art_id, title, article)
    print " [x] Done"
    ch.basic_ack(delivery_tag=method.delivery_tag)


#t, b = download_article('http://www.rabbitmq.com/tutorials/tutorial-two-python.html')

connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
channel = connection.channel()
channel.queue_declare(queue=queue, durable=True)
print ' [*] Waiting for messages. To exit press CTRL+C'
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue=queue)
channel.start_consuming()
