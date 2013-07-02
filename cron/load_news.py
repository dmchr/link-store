#!/usr/bin/env python
import os
import sys

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import config
import mq

DB = config.DB
queue = config.que_update_source
source_limit = 50


def load_news():
    rows = DB.select(
        'sources',
        where="NOW() - INTERVAL 1 HOUR > last_update OR last_update is NULL",
        limit=source_limit
    )
    for source in rows:
        mq.create_job(queue, str(source.id))

load_news()
