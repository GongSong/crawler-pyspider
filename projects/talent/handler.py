#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018-10-31 10:52:45
# Project: test2

from pyspider.helper.date import Date
from pyspider.libs.base_handler import *
from talent.page.rpt import Rpt
from talent.page.tbk import Tbk
from talent.page.upload_to_ai import UploadToAi


class Handler(BaseHandler):
    account_list = ['icy旗舰店', '蔻特信息']  # , '上海奇融', '炫时科技', '优梦投资', '北京穿衣']
    crawl_config = {
    }

    @every(minutes=60)
    def on_start(self):
        # self.crawl_handler_page(UploadToAi('crawler/table/talent/icy旗舰店/2018-12-10--2019-01-08.xls'))
        yesterday = Date.now().plus_days(-1).strftime("%Y-%m-%d")
        for _account in self.account_list:
            self.crawl_handler_page(Rpt(Date.now().plus_days(-30).strftime("%Y-%m-%d"), yesterday, _account))
            self.crawl_handler_page(Tbk(Date.now().plus_days(-60).strftime("%Y-%m-%d"), yesterday, _account))
