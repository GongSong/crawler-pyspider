from backstage_data_migrate.page.sycm.sycm_base import SycmBase
from pyspider.helper.date import Date


class SycmPromAmount:
    """
    概况：本爬虫获取天猫主店的店铺排名和推广状况;
    数据获取的源地址：https://sycm.taobao.com/portal/home.htm ;
    数据获取的接口地址：https://sycm.taobao.com/portal/promotion/getPromotionAmtTrend.json?dateType=day&dateRange=2020-03-10|2020-03-10;
    数据在生意参谋的首页;
    获取内容：【首页】-【管理视窗】-【推广看板】的每日实际推广金额
    """
    URL = 'https://sycm.taobao.com/portal/promotion/getPromotionAmtTrend.json?dateType=day&dateRange={date_range}|{date_range}'

    def __init__(self):
        self.__cookies = None
        self.__fetch_days = 1

    def set_cookies(self, cookies: str):
        """
        设置cookies
        :param cookies:
        :return:
        """
        self.__cookies = cookies
        return self

    def set_fetch_days(self, days: int):
        """
        设置获取近多少天的数据
        :param days:
        :return:
        """
        self.__fetch_days = days
        return self

    def entry(self):
        for _day in range(1, self.__fetch_days + 1):
            date_range = Date.now().plus_days(-_day).format(full=False)
            SycmBase(self.URL.format(date_range=date_range)) \
                .set_unique_define('promotion_amount') \
                .set_cookies(self.__cookies) \
                .set_promotion_date(date_range) \
                .enqueue()
