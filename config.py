import logging
import os
import web

logging.basicConfig()


def is_test():
    if 'WEBPY_ENV' in os.environ:
        return os.environ['WEBPY_ENV'] == 'test'

if is_test():
    DB = web.database(dbn='mysql', host='localhost', db='news_test', user='sot', pw='sot')
else:
    DB = web.database(dbn='mysql', host='localhost', db='linkstore', user='sot', pw='sot')

cache = False

items_per_page = 20
unread_items_per_page = 20

rabbit_host = 'localhost'

# Rabbit queues
que_download_article = 'articles_for_downloads'
que_update_source = 'sources_for_update'

twitter_feed_url = 'http://api.twitter.com/1/statuses/user_timeline.rss?screen_name=%s'
