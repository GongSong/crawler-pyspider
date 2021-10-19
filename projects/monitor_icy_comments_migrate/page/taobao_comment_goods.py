import copy
import json

from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from monitor_icy_comments_migrate.config import *
from cookie.model.data import Data as CookieData


class TaoBaoCommentsGoods(BaseCrawl):
    def __init__(self, goods_url, account, comment_id, delay_time, data):
        super(TaoBaoCommentsGoods, self).__init__()
        self.__shop_type = 1
        self.__account = account
        self.__data = copy.deepcopy(data)
        self.__goods_url = goods_url
        self.__comment_id = comment_id
        self.__delay_time = delay_time

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__goods_url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_BACK_COMMENT, self.__account)) \
            .schedule_priority(SCHEDULE_LEVEL_SECOND) \
            .schedule_delay_second(self.__delay_time) \
            .set_timeout(TIMEOUT) \
            .set_connect_timeout(CONNECT_TIMEOUT) \
            .set_task_id(md5string('taobao_backstage_comment:' + str(self.__comment_id)))

    def parse_response(self, response, task):
        doc = response.text
        json_item = doc.split('JSON.parse(', 1)[1].split(');', 1)[0][1:-1]
        json_item = json.loads(json_item.replace('\\"', '"'))

        goods_id = json_item['baseSnapDO']['itemSnapDO']['itemId']
        barcodes = json_item['baseSnapDO']['itemSnapDO']['spuList']
        barcode = ''
        for code in barcodes:
            if code['name'] == '货号':
                barcode = code['value']

        color = json_item['baseSnapDO']['itemSnapDO']['skuInfoList'][0]['value']
        color = ','.join(color)
        size = json_item['baseSnapDO']['itemSnapDO']['skuInfoList'][1]['value']
        size = ','.join(size)
        details = color + ':' + size
        create_time = Date.now().format()

        self.__data['content']['details'] = details
        self.__data['goodsId'] = goods_id
        self.__data['id'] = barcode
        self.__data['createTime'] = create_time
        self.__data['result'] = doc

        return self.__data
