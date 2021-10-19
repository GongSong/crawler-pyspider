import json

from cookie.model.data import Data as CookieData
from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from weipinhui_migrate.config import *
from weipinhui_migrate.model.weipinhui import Weipinhui


class CatchWeipinhui(BaseCrawl):
    URL = 'http://compass.vis.vip.com/newGoods/details/getDetails?callback=jQuery33107514091226289779_15527447' \
          '32520&brandStoreName=ICY&goodsCode=&sortColumn=goodsAmt&sortType=1&pageSize={}&pageNumber={}&beginD' \
          'ate={}&endDate={}&brandName=%E5%94%AF%E5%93%81%E4%BC%9A%E8%AE%BE%E8%AE%A1%E5%B8%88%E9%9B%86%E5%90%8' \
          '8%E6%97%97%E8%88%B0%E5%BA%97-20190214&surrogateBrandId=303692788&sumType=1&optGroupFlag=0&warehouse' \
          'Flag=0&analysisType=0&selectedGoodsInfo=vipshopPrice%2CorderGoodsPrice&mixBrand=0&dateMode=0&dateTy' \
          'pe=D&detailType=D&dailyDate=&brandType=%E6%97%97%E8%88%B0%E5%BA%97&goodsType=0&dateDim=0&_=15527447' \
          '32551'

    def __init__(self, begin_date, end_date, account, page_num=1, page_size=200):
        """
        唯品会 商品详情 数据
        :param begin_date:
        :param end_date:
        :param account:
        :param page_num:
        :param page_size:
        """
        super(CatchWeipinhui, self).__init__()
        self.__begin_date = begin_date
        self.__end_date = end_date
        self.__page_num = page_num
        self.__page_size = page_size
        self.__account = account
        self.__url = self.URL.format(self.__page_size, self.__page_num,
                                     self.__begin_date, self.__end_date)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_WEIPINHUI, self.__account)) \
            .set_headers_kv('User-Agent', USER_AGENT)

    def parse_response(self, response, task):
        doc = response.text
        try:
            processor_logger.info('获取第：{}页的数据'.format(self.__page_num))
            json_req = doc.split('jQuery33107514091226289779_1552744732520(', 1)[1][:-2]
            content = json.loads(json_req)
            result = content['singleResult']['list']
            if result:
                Weipinhui().update(result, asyncy=True)

                # 抓取下一页
                self.crawl_handler_page(
                    CatchWeipinhui(self.__begin_date, self.__end_date, self.__account, self.__page_num + 1,
                                   self.__page_size))
            else:
                processor_logger.warning('没有第：{}页的数据，退出'.format(self.__page_num))

        except Exception as e:
            processor_logger.exception('第{}页抓取出现错误: {}'.format(self.__page_num, e))
        return {
            'url': self.__url,
            'responseSize': len(response.content),
            'result': response.text
        }
