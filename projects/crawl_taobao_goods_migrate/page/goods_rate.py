import random
import re
import requests
from crawl_taobao_goods_migrate.model.es.es_goods_rate import EsTmallGoodsRate
from crawl_taobao_goods_migrate.model.task import Task
from pyspider.helper.ips_pool import IpsPool
from pyspider.helper.date import Date
from crawl_taobao_goods_migrate.config import *
from pyspider.libs.base_crawl import BaseCrawl
from pyspider.libs.crawl_builder import CrawlBuilder


class GoodsRate(BaseCrawl):
    """
    商品评价分数抓取类
    """

    URL = 'https://dsr-rate.tmall.com/list_dsr_info.htm?itemId={0}&spuId=806781310&sellerId=3165080793&groupId&_ksTS=1562552852233_202&callback=jsonp203'

    def __init__(self, url_or_id, use_proxy=True, priority=0):
        super(GoodsRate, self).__init__()
        self.__headers = {
            "Referer": "https://detail.tmall.com/item.htm",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
        }
        self.__priority = priority
        self.__goods_id = url_or_id.split('id=', 1)[1].split('&', 1)[0] if 'id=' in url_or_id else url_or_id
        self.__use_proxy = use_proxy
        self.__goods_url = url_or_id

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL.format(self.__goods_id)) \
            .set_headers(self.__headers) \
            .schedule_priority(self.__priority) \
            .schedule_age() \
            .set_timeout(GOODS_RATE_TIMEOUT) \
            .set_connect_timeout(GOODS_RATE_CONNECT_TIMEOUT) \
            .set_task_id(Task.get_task_id_goods_rate(self.__goods_id))

        if self.__use_proxy:
            # ip_url = 'http://proxy.httpdaili.com/apinew.asp?sl=10&noinfo=true&ddbh=302094241791519942'
            # _res = requests.get(ip_url).text
            # ip_list = _res.split('\r\n')[:5]
            # ip = random.choice(ip_list)
            # builder.set_proxy(ip)
            builder.set_proxy(IpsPool.get_ip_from_pool())

        return builder

    def parse_response(self, response, task):
        content = response.text
        result = {}
        result['goods_sku'] = self.__goods_id
        result['grade_avg'] = float(re.search('"gradeAvg":(.*?),', content)[1])
        try:
            result['rate_total'] = int(re.search('"rateTotal":(.*?)}', content)[1])
        except:
            result['rate_total'] = 0
        result['sync_time'] = Date.now().format_es_utc_with_tz()
        result['insert_date'] = Date.now().format(full=False)
        result['goods_url'] = self.__goods_url
        EsTmallGoodsRate().update([result], async=True)

        return {
            'unique_name': 'tmall_goods_rate',
            'url': self.URL.format(self.__goods_id),
            'content': response.text
        }

