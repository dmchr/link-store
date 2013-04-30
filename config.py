import web

DB = web.database(dbn='mysql', db='news', user='sot', pw='sot')
cache = False

items_per_page = 5

# Rabbit queues
que_download_article = 'articles_for_downloads'
que_update_source = 'sources_for_update'