#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2021-04-22 10:10:26
# Project: landong
from landong.page.bas_band import BaseBrand
from landong.page.bas_product_category import BasProductCategory
from landong.page.bas_product_color import BaseProductColor
from landong.page.corn.corn import BaiDu
from landong.page.get_pattern_size_group import GetPatternSizeGroup
from landong.page.pattern_design import PatternDesign
from pyspider.libs.base_handler import *
from landong.page.plm_mass_pattern_design import MassPatternDesign


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    @every(minutes=5)
    def bas_brand(self):
        """
        爬取波段档案
        :return:
        """
        self.crawl_handler_page(BaseBrand(next_page=True))

    @every(minutes=5)
    def product_color(self):
        """
        颜色档案
        :return:
        """
        self.crawl_handler_page(BaseProductColor(next_page=True))

    @every(minutes=5)
    def mass_pattern_design(self):
        """
        拉取澜东商品档案
        """
        self.crawl_handler_page(MassPatternDesign(next_page=True).set_crawl_host("page_host"))

    @every(minutes=5)
    def bas_pattern_size(self):
        """
        拉取澜东云尺码档案
        """
        self.crawl_handler_page(GetPatternSizeGroup().set_crawl_host("page_host"))

    @every(minutes=5)
    def size_from_redis_to_tg(self):
        """
        定时更新澜东云尺码数据从redis到ES
        """
        self.crawl_handler_page(BaiDu(type_corn="size"))

    @every(minutes=5)
    def bas_product_category(self):
        """
        拉取澜东云品类档案
        """
        self.crawl_handler_page(BasProductCategory(next_page=True))

    @every(minutes=5)
    def pattern_design(self):
        """
        新款档案 - 新增编辑商品设计
        :return:
        """
        self.crawl_handler_page(PatternDesign(next_page=True))
