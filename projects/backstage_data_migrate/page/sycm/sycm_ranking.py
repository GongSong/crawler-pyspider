from backstage_data_migrate.page.sycm.sycm_base import SycmBase
from pyspider.helper.date import Date


class SycmRanking:
    """
    概况：本爬虫获取天猫主店的店铺排名;
    数据获取的源地址：https://sycm.taobao.com/portal/home.htm ;
    数据获取的接口地址：https://sycm.taobao.com/portal/month/overview.json?dateType=day&dateRange=2020-03-10%7C2020-03-10&sellerType=online&_=1583913384946&token=1aa656228 ;
    数据在生意参谋的首页;
    获取内容：店铺概况的近30天支付金额排行
    """
    URL = 'https://sycm.taobao.com/portal/month/overview.json?dateType=day&dateRange={date_range}|{date_range}'

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
                .set_unique_define('sync_ranking') \
                .set_cookies(self.__cookies) \
                .set_ranking_date(date_range) \
                .enqueue()
