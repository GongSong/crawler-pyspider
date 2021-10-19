#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2019-05-05 16:22:59
# Project: blog_spider
from blog_spider.config import *
from blog_spider.page.weibo_blogger_id import WeiboBloggerId
from blog_spider.page.weibo_topic import WeiboTopic
from pyspider.helper.date import Date
from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    def catch_weibo_topic(self):
        words = '游戏开发'
        queue_data = {
            "type": 1,
            "accountKey": "",
            "keywords": [words],
            "status": 2
        }
        self.crawl_handler_page(WeiboTopic(words, priority=PRIORITY_FIRST, to_next_page=True, queue_data=queue_data))

    def catch_weibo_blogger(self):
        blogger_id = '1969176463'
        queue_data = {
            "type": 1,
            "accountKey": "1715118170",
            "keywords": [],
            "status": 2
        }
        self.crawl_handler_page(
            WeiboBloggerId(blogger_id, priority=PRIORITY_FIRST, to_next_page=False, queue_data=queue_data))

    def send_middle_queue_msg(self):
        from mq_handler import CONST_MESSAGE_TAG_BLOG_SYNC_ACT
        from mq_handler import CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        accout_list = ["2622105561"]
        for i in accout_list:
            data_id = i
            data = {
                "type": 1,
                "accountKey": data_id,
                "status": 1
            }
            MQ().publish_message(CONST_MESSAGE_TAG_BLOG_SYNC_ACT, data, data_id, Date.now().timestamp(),
                                 CONST_ACTION_UPDATE)
