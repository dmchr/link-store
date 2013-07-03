#!/usr/bin/env python
# -*- coding: utf-8 -*-
import opml
import os
import sys

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import config
from models.source import SourceFactory

DB = config.DB
logger = config.logger


def parse_user_opml(user_id, source):
    source = source.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
    try:
        res = opml.from_string(source)
    except Exception as exc:
        logger.error(exc)
        return False
    if res:
        for category in res:
            logger.debug('Category: %s' % category.text)
            for item in category:
                logger.debug('Item: %s %s' % (item.text, item.xmlUrl))
                SourceFactory().add_to_user(user_id, 'feed', item.xmlUrl, item.text, category.text)
        return True
    return False


def get_users_opml():
    return DB.select(
        'user_opml',
        where='is_handled=0'
    )


def set_opml_handled(opml_id):
    return DB.update(
        'user_opml',
        where='id=$id',
        vars={
            'id': opml_id
        },
        is_handled=1
    )


logger.info('Start handling OPML')
logger.info('-------------------')
for item in get_users_opml():
    if parse_user_opml(item.user_id, item.opml):
        set_opml_handled(item.id)
logger.info('End handling OPML')
