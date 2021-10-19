import json
import uuid

from backstage_data_migrate.model.es.sycm_promotion_amount import SycmPromAmount
from backstage_data_migrate.model.es.sycm_shop_ranking import SycmShopRanking
from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from backstage_data_migrate.config import *


class SycmBase(BaseCrawl):
    """
    概况：这是天猫生意参谋后台爬虫的基类;
    生意参谋的首页地址: https://sycm.taobao.com/portal/home.htm ;
    """

    def __init__(self, url):
        super(SycmBase, self).__init__()
        self.__url = url
        self.__unique_define = md5string(self.__url)
        self.__cookies = None
        self.__ranking_date = None
        self.__promotion_date = None

    def set_unique_define(self, unique_flag):
        """
        设置唯一标识
        :param unique_flag:
        :return:
        """
        self.__unique_define = '{}:{}'.format(unique_flag, md5string(self.__url + str(uuid.uuid4())))
        return self

    def set_cookies(self, cookies: str):
        """
        设置cookie
        :param cookies:
        :return:
        """
        self.__cookies = cookies
        return self

    def set_ranking_date(self, ranking_date: str):
        """
        如果有店铺排名获取日期，则把数据保存到对应的es
        :param ranking_date:
        :return:
        """
        self.__ranking_date = ranking_date
        return self

    def set_promotion_date(self, promotion_date: str):
        """
        如果有店铺推广实际金额获取日期，则把数据保存到对应的es
        :param promotion_date:
        :return:
        """
        self.__promotion_date = promotion_date
        return self

    def crawl_builder(self):
        buidler = CrawlBuilder() \
            .set_url('{url}#{unique_define}'.format(url=self.__url, unique_define=self.__unique_define)) \
            .set_headers_kv('User-Agent', USER_AGENT)
        if self.__cookies:
            buidler.set_cookies(self.__cookies)
        return buidler

    def parse_response(self, response, task):
        sync_time = Date.now().format_es_utc_with_tz()
        if self.__ranking_date:
            # 有店铺排名获取日期，把数据保存到对应的es
            resp = json.loads(response.text)
            save_dict = {
                'ranking_date': self.__ranking_date,
                'shop_ranking': resp['content']['data']['rank'],
                'sync_time': sync_time,
            }
            SycmShopRanking().update([save_dict], async=True)
        elif self.__promotion_date:
            # 有店铺推广实际金额获取日期，把数据保存到对应的es
            save_list = []
            resp = json.loads(response.text)
            promotion_amounts = resp['content']['data']['promotionCntAmt']
            for index, amount in enumerate(promotion_amounts):
                save_dict = {
                    'promotion_date': Date.now().plus_days(index - len(promotion_amounts)).format(full=False),
                    'promotion_account': amount,
                    'sync_time': sync_time,
                }
                save_list.append(save_dict)
            SycmPromAmount().update(save_list, async=True)

        return {
            'url': self.__url,
            # 'content': response.text,
            'sync_time': sync_time,
        }
