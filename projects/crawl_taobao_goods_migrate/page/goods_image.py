import copy
import json

from crawl_taobao_goods_migrate.model.task import Task
from pyspider.libs.base_crawl import *
from crawl_taobao_goods_migrate.config import *
from pyspider.helper.ips_pool import IpsPool

from crawl_taobao_goods_migrate.page.goods_callback import GoodsCallback


class GoodsImage(BaseCrawl):
    """
    商品图片抓取类
    """

    DES_URL = 'https://h5api.m.taobao.com/h5/mtop.taobao.detail.getdesc/6.0/?jsv=2.4.11&appKey=12574478&t=' \
                  '1546930070435&sign=cecda9a00277bb2375c3c0b37655c169&api=mtop.taobao.detail.getdesc&v=6.0&ty' \
                  'pe=jsonp&dataType=jsonp&timeout=20000&callback=mtopjsonp1&data=%7B%22id%22%3A%22{}%22%2C%22' \
                  'type%22%3A%220%22%2C%22f%22%3A%22TB1jTRMAlLoK1RjSZFu8qtn0Xla%22%7D'

    def __init__(self, goods_id, user_proxy, save_dict, callback_link='', priority=0):
        super(GoodsImage, self).__init__()
        self.__goods_id = goods_id
        self.__user_proxy = user_proxy
        self.__data = copy.deepcopy(save_dict)
        self.__priority = priority
        self.__callback_link = callback_link

    def crawl_builder(self):
        des_url = self.DES_URL.format(self.__goods_id)
        builder = CrawlBuilder() \
                    .set_url(des_url) \
                    .set_headers_kv('User-Agent', USER_AGENT) \
                    .schedule_priority(self.__priority) \
                    .schedule_age() \
                    .set_timeout(GOODS_TIMEOUT) \
                    .set_connect_timeout(GOODS_CONNECT_TIMEOUT) \
                    .set_task_id(Task.get_task_id_goods_image(self.__goods_id))

        if self.__user_proxy:
            builder.set_proxy(IpsPool.get_ip_from_pool())

        return builder

    def parse_response(self, response, task):
        content = response.text

        processor_logger.info('des_img_text: {}'.format(content))
        des_img_info = '{"api"' + content.split('{"api"', 1)[1][:-1]
        des_img_info = json.loads(des_img_info)
        des_img_urls = des_img_info.get('data').get('wdescContent').get('pages')
        des_image = ['https://img.alicdn.com' + url.split('img.alicdn.com', 1)[1].replace('</img>', '')
                     for url in des_img_urls if '<img size' in url and 'img.alicdn.com' in url]

        self.__data['des_image'] = des_image
        self.__data['url'] = response.url
        self.__data['content'] = content
        self.__data['callback_link'] = self.__callback_link
        self.__data['excelSize'] = len(response.content)

        return self.__data

    def result_hook(self, result, task):
        if self.__callback_link:
            self.crawl_handler_page(GoodsCallback(self.__callback_link, priority=self.__priority))
            processor_logger.info("已请求回调链接：{}".format(self.__callback_link))
