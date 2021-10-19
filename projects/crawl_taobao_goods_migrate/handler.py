#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018-10-31 10:52:45
# Project: crawl_taobao_goods_migrate
from crawl_taobao_goods_migrate.model.es.es_based_spu_summary import EsBasedSpuSummary
from crawl_taobao_goods_migrate.page.goods_rate import GoodsRate
from pyspider.libs.base_handler import *
from crawl_taobao_goods_migrate.model.result import Result
from crawl_taobao_goods_migrate.page.goods_details import GoodsDetails
from crawl_taobao_goods_migrate.page.shop_details import ShopDetails


class Handler(BaseHandler):
    crawl_config = {
    }

    # @every(minutes=60*24)
    def on_start(self):
        pass

    # @every(minutes=60*24)
    def goods_polling(self):
        """
        由于商铺数据过多，轮询入口放到了cron.py， 此处不进行轮询
        轮询所有的天猫商品详情
        :return:
        """
        goods = ["591886467387"]
        processor_logger.warning('需要轮询的商品总数为: {}'.format(len(goods)))
        for goods_id in goods:
            # 轮询所有的商品
            self.crawl_handler_page(GoodsDetails(goods_id, use_proxy=False))

    # @every(minutes=60*24)
    def shop_polling(self):
        """
        已失效，无法抓取到天猫店铺的数据了
        :return:
        """
        shops = Result().find_all_shop_id()
        processor_logger.warning('需要轮询的店铺总数为: {}'.format(shops.count()))
        for shop in shops:
            shop_id = shop.get('result').get('shop_id')
            shop_url = 'https://shop{}.taobao.com'.format(shop_id)
            processor_logger.info('抓取 shop url: {}'.format(shop_url))
            # 轮询所有的商品
            self.crawl_handler_page(ShopDetails(shop_url))

    # @every(minutes=60*24)
    def goods_rate_polling(self):
        """
        已失效，无法抓取到天猫商品的数据
        :return:
        """
        goods_list = EsBasedSpuSummary().scroll(page_size=200)
        for _list in goods_list:
            for _item in _list:
                goods_id = _item.get('tmallGoodsId', '')
                if goods_id:
                    goods_url = 'https://detail.tmall.com/item.htm?id=' + str(goods_id)
                    self.crawl_handler_page(GoodsRate(goods_url))

