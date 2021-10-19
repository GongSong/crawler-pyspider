#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2019-03-22 17:00:19
# Project: hupun_api
from hupun_api.page.order import OrderApi
from pyspider.helper.date import Date
from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    # @every(minutes=1)
    def crawl_order_api(self):
        """
        抓取订单API数据的入口
        :return:
        """
        start_page = 1
        page_size = 200
        modify_hour = 0.1
        modify_time = Date.now().plus_hours(-modify_hour).millisecond()
        self.crawl_handler_page(
            OrderApi(to_next_page=True)
                .set_param('page', start_page)
                .set_param('limit', page_size)
                .set_param('modify_time', modify_time)
        )

    def crawl_all_order_api(self):
        """
        抓取订单API数据的入口，全量数据
        :return:
        """
        start_page = 1
        page_size = 200
        for day in range(5, 1096, 5):
            modify_time = Date.now().plus_days(-day).to_day_start().millisecond()
            end_time = Date.now().plus_days(-day + 5).to_day_end().millisecond()
            print('modify_time', modify_time)
            print('end_time', end_time)
            self.crawl_handler_page(
                OrderApi(to_next_page=True)
                    .set_param('page', start_page)
                    .set_param('limit', page_size)
                    .set_param('modify_time', modify_time)
                    .set_param('end_time', end_time)
            )
