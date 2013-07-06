import logging
import os
import web

log_level = logging.DEBUG
logger = logging.getLogger('main')
logger.setLevel(log_level)
ch = logging.StreamHandler()
ch.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def is_test():
    if 'WEBPY_ENV' in os.environ:
        return os.environ['WEBPY_ENV'] == 'test'

if is_test():
    DB = web.database(dbn='mysql', host='localhost', db='news_test', user='sot', pw='sot')
else:
    DB = web.database(dbn='mysql', host='localhost', db='linkstore', user='sot', pw='sot')

cache = False

socket_timeout = 5

items_per_page = 20
unread_items_per_page = 20

rabbit_host = '127.0.0.1'

# Rabbit queues
que_download_article = 'articles_for_downloads'
que_update_source = 'sources_for_update'

twitter_feed_url = 'http://api.twitter.com/1/statuses/user_timeline.rss?screen_name=%s'

default_source_category = 'No category'
