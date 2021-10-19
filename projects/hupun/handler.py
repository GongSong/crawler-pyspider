#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2019-01-28 07:10:16
# Project: hupun
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun.page.hupun_goods.goods_information import GoodsInformation
from hupun.page.in_sale_store_table.table_export import StatementExport
from hupun.page.purchase_order import PurchaseOrder
from hupun.page.purchase_store_order import PurchaseStoreOrder
from cookie.model.data import Data as CookieData
from pyspider.libs.base_handler import *
from hupun.page.order import Order
from pyspider.helper.date import Date
import json


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        self.order_newly_10min()
        # Order.run_days('2018-10-01', '2019-01-01', 29)
        # Order.run_days('2018-06-01', '2018-10-01', 25)
        # Order.run_days('2018-01-01', '2018-06-01', 20)
        # Order.run_days('2017-03-01', '2018-01-01', 15)


    # @every(minutes=1)
    def update_cookie(self):
        cookies_dict = []
        # for _ in CookiesPool.get_cookies_from_pool('hupun', '万里牛:测试'):
        #     cookies_dict.setdefault(_['name'], _['value'])
        # cookies_str = "; ".join([str(x) + "=" + str(y) for x, y in cookies_dict.items()])
        save_cookies = []
        for _cookie in cookies_dict:
            save_cookies.append({'name': _cookie['name'], 'value': _cookie['value']})
        save_cookies = json.dumps(save_cookies)
        CookieData.set(CookieData.CONST_PLATFORM_TAOBAO_SHOP, CookieData.CONST_USER_TAOBAO_SHOP[0][0], save_cookies)

    @every(minutes=2)
    def order_newly_10min(self):
        """
        每2分钟更新近十分钟的数据
        :return:
        """
        self.crawl_handler_page(
            Order(go_next_page=True).set_start_time(Date.now().plus_minutes(-10).format()).set_priority(
                Order.CONST_PRIORITY_FIRST)
        )

    @every(minutes=10)
    def order_newly_1h(self):
        """
        每10分钟更新最近1小时的订单
        :return:
        """
        self.crawl_handler_page(
            Order(go_next_page=True).set_start_time(Date.now().plus_hours(-1).format()).set_priority(
                Order.CONST_PRIORITY_FIRST)
        )

    @every(minutes=60)
    def order_newly_1w(self):
        """
        每60分钟更新最近1周的订单
        :return:
        """
        self.crawl_handler_page(
            Order(go_next_page=True, schedule_age=3600 * 2).set_start_time(
                Date.now().plus_days(-7).to_day_start().format()).set_priority(Order.CONST_PRIORITY_SECOND)
        )

    @every(minutes=60 * 6)
    def order_newly_1m(self):
        """
        每6小时更新最近1个月的订单
        :return:
        """
        self.crawl_handler_page(
            Order(go_next_page=True, schedule_age=3600 * 2).set_start_time(
                Date.now().plus_days(-30).to_day_start().format()).set_priority(Order.CONST_PRIORITY_THIRD)
        )

    @every(minutes=60 * 24)
    def order_newly_3m(self):
        """
        每天更新最近3个月的订单
        :return:
        """
        self.crawl_handler_page(
            Order(go_next_page=True, catch_details=False).set_start_time(
                Date.now().plus_days(-90).to_day_start().format()).set_priority(Order.CONST_PRIORITY_THIRD)
        )

    @every(minutes=30)
    def purchase_store_order_1d(self):
        """
        每 30 分钟更新近 3 天的 采购入库单
        :return:
        """
        self.crawl_handler_page(
            PurchaseStoreOrder(go_next_page=True).set_start_time(
                Date.now().plus_days(-2).to_day_start().format()).set_priority(PurchaseStoreOrder.CONST_PRIORITY_FIRST))

    @every(minutes=30)
    def purchase_order_1d(self):
        """
        半小时更新一次 采购订单 近一天的数据
        :return:
        """
        self.crawl_handler_page(PurchaseOrder(True).set_start_time(Date.now().format()).set_priority(
            PurchaseOrder.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 24)
    def purchase_order_3m(self):
        """
        每天更新一次 采购订单 近三个月 的数据
        :return:
        """
        self.crawl_handler_page(PurchaseOrder(True).set_start_time(Date.now().plus_days(-90).format()).set_priority(
            PurchaseOrder.CONST_PRIORITY_FIRST))

    @every(minutes=60)
    def goods_information(self):
        """
        每小时更新一次商品信息的数据
        :return:
        """
        self.crawl_handler_page(GoodsInformation(go_next_page=True).set_priority(GoodsInformation.CONST_PRIORITY_FIRST))

    def in_sale_store_table(self):
        """
        进销存报表下载
        :return:
        """
        storage_ids = StoreHouse().get_storage_ids()
        storage_uids = ','.join(storage_ids) + ','
        self.crawl_handler_page(
            StatementExport(storage_uids).set_start_time(Date.now().plus_days(-1).format()).set_end_time(
                Date.now().plus_days(-1).format()))

    def break_order_fetch(self):
        """
        跳出订单的所有循环下一页抓取
        重要：调用该方法之后记得取消cancel_break_order_fetch, 否则就不会下一页下一页的爬了
        :return:
        """
        Order.set_flag(Order.CONST_FLAG_BREAK)

    def cancel_break_order_fetch(self):
        """
        取消跳出订单循环
        :return:
        """
        Order.set_flag(Order.CONST_FLAG_NONE)
