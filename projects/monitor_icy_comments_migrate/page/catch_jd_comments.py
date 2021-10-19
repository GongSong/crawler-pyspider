from monitor_icy_comments_migrate.config import *
from monitor_icy_comments_migrate.page.store_jd_exists import StoreJDExists
from pyspider.libs.base_crawl import *


class CatchJDComments(BaseCrawl):
    URL = 'https://item.jd.com/{}.html'

    def __init__(self, goods_id, barcode):
        super(CatchJDComments, self).__init__()
        self.__goods_id = goods_id
        self.__jd_url = self.URL.format(self.__goods_id)
        self.__barcode = barcode
        self.__shop_type = 3

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__jd_url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_priority(SCHEDULE_LEVEL_FIRST)

    def parse_response(self, response, task):
        content = response.text
        new_url = response.url
        if str(self.__goods_id) not in new_url:
            processor_logger.info("商品: {} 已下架".format(self.__goods_id))
            return {
                'msg': "商品: {} 已下架".format(self.__goods_id),
                'jd_goods_id': self.__goods_id,
                'redirect_url': new_url,
            }
        else:
            shop_id = self.get_jd_shop_id(content)
            if shop_id and shop_id == JD_ICY_SHOP_ID:
                self.crawl_handler_page(StoreJDExists(self.__goods_id, self.__barcode))
            else:
                processor_logger.info('非 icy 商品: {}，跳过抓取'.format(self.__goods_id))
                return {
                    'msg': '非 icy 商品: {}，跳过抓取'.format(self.__goods_id),
                    'jd_goods_id': self.__goods_id,
                    'redirect_url': new_url,
                }

    def get_jd_shop_id(self, content):
        """
        从响应结果中提取 shop id
        :param content:
        :return:
        """
        shop_id = ''
        try:
            shop_id = content.split("shopId:'", 1)[1].split("',", 1)[0]
        except Exception as e:
            processor_logger.error(e)
        return shop_id
