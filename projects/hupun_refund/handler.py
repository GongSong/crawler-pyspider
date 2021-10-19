#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2019-01-28 07:10:16
# Project: hupun
from hupun_refund.page.order_refund import OrderRefund
from hupun_refund.page.taobao_refund import TaobaoRefund
from pyspider.libs.base_handler import *
from pyspider.helper.date import Date


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    @every(minutes=10)
    def taobao_refund_30min(self):
        """
        每 10 分钟更新近 30 分钟的 淘宝售后单 的数据
        :return:
        """
        self.crawl_handler_page(TaobaoRefund(True).set_start_time(Date.now().plus_minutes(-30).format()).set_priority(
            TaobaoRefund.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 4)
    def taobao_refund_1d(self):
        """
        每 4 小时更新近 1 天的 淘宝售后单 的数据
        :return:
        """
        self.crawl_handler_page(TaobaoRefund(True).set_start_time(Date.now().plus_days(-1).format()).set_priority(
            TaobaoRefund.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 24)
    def taobao_refund_1m(self):
        """
        每 6 小时更新近 30 天的 淘宝售后单 的数据
        :return:
        """
        self.crawl_handler_page(TaobaoRefund(True).set_start_time(Date.now().plus_days(-30).format()).set_priority(
            TaobaoRefund.CONST_PRIORITY_FIRST))

    @every(minutes=10)
    def order_refund_30min(self):
        """
        每十分钟更新 商品售后单 近 30 分钟的数据的数据
        :return:
        """
        self.crawl_handler_page(OrderRefund(True).set_start_time(Date.now().plus_minutes(-30).format()).set_priority(
            OrderRefund.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 4)
    def order_refund_1d(self):
        """
        每 4h 更新 商品售后单 近 1 天的数据的数据
        :return:
        """
        self.crawl_handler_page(OrderRefund(True).set_start_time(Date.now().plus_days(-1).format()).set_priority(
            OrderRefund.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 24)
    def order_refund_3m(self):
        """
        每 24h 更新 商品售后单 近 3 个月的数据的数据
        :return:
        """
        self.crawl_handler_page(OrderRefund(True).set_start_time(Date.now().plus_days(-90).format()).set_priority(
            OrderRefund.CONST_PRIORITY_FIRST))
