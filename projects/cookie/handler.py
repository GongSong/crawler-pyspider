#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2019-03-05 10:53:02
# Project: cookie
from cookie.page.hupun_cookie_check import HCookieCheck
from cookie.page.hupun_login_account import HupunLoginAccount
from cookie.page.landong.landong_check import LandongCookieCheck
from cookie.page.landong.landong_login import LandongLogin
from pyspider.libs.base_handler import *
from cookie.model.data import Data as CookieData


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        self.hupun_cookie_maintain()

    @every(minutes=1)
    def hupun_cookie_maintain(self):
        for index, account in enumerate(CookieData.CONST_USER_HUPUN):
            username = account[0]
            password = account[1]
            self.crawl_handler_page(HCookieCheck(username, password).set_priority(HCookieCheck.CONST_PRIORITY_BUNDLED).set_cookie_position(index))

    @every(minutes=10)
    def force_update_cookie(self):
        for i in range(3, 6):
            account = CookieData.CONST_USER_HUPUN[i]
            username = account[0]
            password = account[1]
            self.crawl_handler_page(HupunLoginAccount(username, password))

    @every(minutes=60)
    def force_update_cookie_1(self):
        account = CookieData.CONST_USER_HUPUN[1]
        username = account[0]
        password = account[1]
        self.crawl_handler_page(HupunLoginAccount(username, password))

    def landong_cookie_maintain(self):
        """
        检测澜东云的cookie是否过期
        过期则重新登录
        :return:
        """
        for index, account in enumerate(CookieData.CONST_USER_LANDONG):
            username = account[0]
            password = account[1]
            self.crawl_handler_page(LandongCookieCheck(username, password).set_cookie_position(index))

    def force_update_landong_cookies(self):
        """
        强制更新澜东云的cookies
        :return:
        """
        for i in range(0, 1):
            account = CookieData.CONST_USER_LANDONG[i]
            username = account[0]
            password = account[1]
            self.crawl_handler_page(LandongLogin(username, password))
