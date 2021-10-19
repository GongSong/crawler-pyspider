import unittest

from cookie.model.data import Data
from pyspider.helper.date import Date
from taobao_tables_download.page.shop_all_day import ShopAllDay
from taobao_tables_download.page.shop_all_month import ShopAllMonth
from taobao_tables_download.page.shop_all_week import ShopAllWeek
from taobao_tables_download.page.shop_category_day import ShopCategoryDay
from taobao_tables_download.page.shop_category_week import ShopCategoryWeek
from taobao_tables_download.page.shop_category_month import ShopCategoryMonth
from taobao_tables_download.page.shop_flow_day import ShopFlowDay
from taobao_tables_download.page.shop_flow_week import ShopFlowWeek
from taobao_tables_download.page.shop_flow_month import ShopFlowMonth
from taobao_tables_download.page.shop_hour_day import ShopHourDay
from taobao_tables_download.page.shop_keyword_day import ShopKeywordDay


class Test(unittest.TestCase):
    """
    测试之前需要先获取cookie
    """

    def test_shop_all_day(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_整体_自然日_自动更新', today])
        start_date_day = Date.now().plus_days(-30).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopAllDay(file_name, start_date_day, end_date, _usr, _channel).test()

    def test_shop_all_month(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_整体_自然月_自动更新', today])
        start_date_month = Date.now().to_month_start().plus_months(-6).format(full=False)
        end_date_month = Date.now().plus_months(-1).to_month_end().format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopAllMonth(file_name, start_date_month, end_date_month, _usr, _channel).test()

    def test_shop_all_week(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_整体_自然周_自动更新', today])
        start_date_week = Date.now().plus_days(-56).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopAllWeek(file_name, start_date_week, end_date, _usr, _channel).test()

    def test_shop_category_day(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_类目构成_自然日_自动更新', today])
        start_date_day = Date.now().plus_days(-30).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopCategoryDay(file_name, start_date_day, end_date, _usr, _channel).test()

    def test_shop_category_week(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_类目构成_自然周_自动更新', today])
        start_date_week = Date.now().plus_days(-56).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopCategoryWeek(file_name, start_date_week, end_date, _usr, _channel).test()

    def test_category_month(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_类目构成_自然月_自动更新', today])
        start_date_month = Date.now().to_month_start().plus_months(-6).format(full=False)
        end_date_month = Date.now().plus_months(-1).to_month_end().format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopCategoryMonth(file_name, start_date_month, end_date_month, _usr, _channel).test()

    def test_shop_flow_day(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_流量来源_自然日_自动更新', today])
        start_date_day = Date.now().plus_days(-30).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopFlowDay(file_name, start_date_day, end_date, _usr, _channel).test()

    def test_shop_flow_week(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_流量来源_自然周_自动更新', today])
        start_date_week = Date.now().plus_days(-56).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopFlowWeek(file_name, start_date_week, end_date, _usr, _channel).test()

    def test_shop_flow_month(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_流量来源_自然月_自动更新', today])
        start_date_month = Date.now().to_month_start().plus_months(-6).format(full=False)
        end_date_month = Date.now().plus_months(-1).to_month_end().format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopFlowMonth(file_name, start_date_month, end_date_month, _usr, _channel).test()

    def test_shop_hour_day(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_分小时_自然日_自动更新', today])
        start_date_day = Date.now().plus_days(-30).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopHourDay(file_name, start_date_day, end_date, _usr, _channel).test()

    def test_shop_keyword_day(self):
        day = 1
        today = Date.now().plus_days(1 - day).format(full=False)
        file_name = 'T'.join(['店铺_引流关键词_自然日_自动更新', today])
        start_date_day = Date.now().plus_days(-30).format(full=False)
        end_date = Date.now().plus_days(-day).format(full=False)
        _usr, _pwd, _channel = Data.CONST_USER_SYCM_BACKSTAGE[0]
        assert ShopKeywordDay(file_name, start_date_day, end_date, _usr, _channel).test()


if __name__ == '__main__':
    unittest.main()
