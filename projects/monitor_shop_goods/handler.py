#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018-11-12 12:02:45
# Project: monitor_shop_goods
import io
import requests
import json

from pyspider.libs.base_handler import *
from pyspider.helper.logging import processor_logger
from monitor_shop_goods.model.shop import Shop
from monitor_shop_goods.page.shelf_app import ShelfApp
from monitor_shop_goods.page.shelf_jd import ShelfJD
from monitor_shop_goods.page.shelf_redbook import ShelfRedBook
from monitor_shop_goods.page.shelf_taobao import ShelfTaoBao
from monitor_shop_goods.page.shelf_tmall import ShelfTmall


class Handler(BaseHandler):
    crawl_config = {
    }

    CONSTANT_TAOBAO = 1
    CONSTANT_TMALL = 2
    CONSTANT_JD = 3
    CONSTANT_REDBOOK = 4
    CONSTANT_APP = 5

    @every(minutes=60)
    def on_start(self):
        """
        项目 监控icy的五个渠道商品上下架 爬虫入口
        :return:
        """
        pass

    @every(minutes=60)
    def shelf_taobao(self):
        goods_ids = self.get_mongo_data(self.CONSTANT_TAOBAO)
        if goods_ids is None:
            pass
        else:
            processor_logger.info('正在检测淘宝商品上下架状态')
            for _goods_id in goods_ids:
                self.crawl_handler_page(ShelfTaoBao(_goods_id))

    @every(minutes=60)
    def shelf_tamll(self):
        goods_ids = self.get_mongo_data(self.CONSTANT_TMALL)
        if goods_ids is None:
            pass
        else:
            processor_logger.info('正在检测天猫商品上下架状态')
            for _goods_id in goods_ids:
                self.crawl_handler_page(ShelfTmall(_goods_id))

    @every(minutes=60)
    def shelf_jd(self):
        goods_ids = self.get_mongo_data(self.CONSTANT_JD)
        if goods_ids is None:
            pass
        else:
            processor_logger.info('正在检测京东商品上下架状态')
            for _goods_id in goods_ids:
                self.crawl_handler_page(ShelfJD(_goods_id))

    @every(minutes=60)
    def shelf_redbook(self):
        goods_ids = self.get_mongo_data(self.CONSTANT_REDBOOK)
        if goods_ids is None:
            pass
        else:
            processor_logger.info('正在检测小红书商品上下架状态')
            for _goods_id in goods_ids:
                self.crawl_handler_page(ShelfRedBook(_goods_id))

    @every(minutes=60)
    def shelf_app(self):
        goods_ids = self.get_mongo_data(self.CONSTANT_APP)
        if goods_ids is None:
            pass
        else:
            processor_logger.info('正在检测app商品上下架状态')
            for _goods_id in goods_ids:
                self.crawl_handler_page(ShelfApp(_goods_id))

    def get_mongo_data(self, type):
        """
        根据店铺类型返回对应的商品URL列表
        :param type:
        :return: list
        """
        goods_id_list = list()
        data = {
            'goods_type': type,
        }
        shop = Shop().find(data)
        if shop.count() == 0:
            processor_logger.info('there isn\'t goods url in shop type:{}'.format(type))
        else:
            for g in shop:
                goods_id = g.get('goods_id')
                status = g.get('status')
                processor_logger.info('goods_id : {}'.format(goods_id))
                processor_logger.info('status : {}'.format(status))
                goods_id_list.append(goods_id)
        return goods_id_list

