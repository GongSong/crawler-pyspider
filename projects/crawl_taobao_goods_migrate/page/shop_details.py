import re

from crawl_taobao_goods_migrate.model.task import Task
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from crawl_taobao_goods_migrate.config import *

from crawl_taobao_goods_migrate.page.shop_callback import ShopCallback


class ShopDetails(BaseCrawl):
    """
    店铺详情抓取类
    """

    def __init__(self, shop_url, callback_link='', priority=0):
        super(ShopDetails, self).__init__()
        self.__shop_url = shop_url
        self.__shop_id = shop_url.split('//shop', 1)[1].split('.taobao.com', 1)[0]
        self.__priority = priority
        self.__callback_link = callback_link

    def crawl_builder(self):
        builder = CrawlBuilder() \
                    .set_url(self.__shop_url) \
                    .set_headers_kv('User-Agent', USER_AGENT) \
                    .schedule_priority(self.__priority) \
                    .schedule_age() \
                    .set_timeout(10) \
                    .set_task_id(Task.get_task_id_shop_details(self.__shop_id))

        return builder

    def parse_response(self, response, task):
        doc = response.doc
        content = response.text

        # ------------------ 解析店铺的 banner 图 等详情 ------------------
        # 店铺平台
        platform = 1

        # 店铺名称
        try:
            shop_name = doc('a.shop-name')('span').text().strip()
        except Exception as e:
            processor_logger.error('解析shop name出错：{}'.format(e))
            shop_name = ''

        # 店铺的真实地址
        real_url_1 = doc('a.shop-name-link')
        real_url_2 = doc('a.logo-extra.iconfont')
        if real_url_1:
            shop_url = real_url_1.attr('href')
        elif real_url_2:
            shop_url = real_url_2.attr('href')
        else:
            processor_logger.warning('获取店铺的真实地址失败')
            return {
                'error_msg': 'failed to get shop real url',
                'save': response.save,
                'excelSize': len(response.content),
                'result': content
            }
        if 'http' not in shop_url:
            shop_url = 'https:' + shop_url

        # 店铺数据更新时间
        update_time = Date.now().format()

        # 店铺首页banner图
        banner_imgs = []

        # 首页的TB2图
        content = content.replace('\\"', '')
        pattern = re.compile('data-ks-lazyload="(.*?)"', re.S)
        urls = pattern.findall(content)
        if urls:
            for url in urls:
                if 'XXXXX' not in url and 'TB2' in url:
                    banner_imgs.append('https:' + url)

        # 获取轮播图
        lun_pattern = re.compile('image:url\((.*?)\);', re.S)
        lun_urls = lun_pattern.findall(content)
        if lun_urls:
            for url in lun_urls:
                if 'TB2' in url and "XXXXX" not in url:
                    banner_imgs.append('https:' + url)

        # 获取轮播图
        lun_pattern_1 = re.compile('background:url\((.*?)\)', re.S)
        lun_urls_1 = lun_pattern_1.findall(content)
        if lun_urls_1:
            for url in lun_urls_1:
                if 'TB2' in url and "XXXXX" not in url and '.gif' not in url:
                    banner_imgs.append('https:' + url)

        # 获取轮播图
        lun_pattern_2 = re.compile('url\((.*?)\)', re.S)
        lun_urls_2 = lun_pattern_2.findall(content)
        if lun_urls_2:
            for url in lun_urls_2:
                if 'TB2' in url and "XXXXX" not in url and '.gif' not in url:
                    banner_imgs.append('https:' + url)

        banner_handle_pic = []
        for img in banner_imgs:
            if len(img.split('jpg')) > 2:
                banner_handle_pic.append(img.split('jpg')[0] + 'jpg')
            else:
                banner_handle_pic.append(img)

        processor_logger.info('banner_handle_pic: {}'.format(banner_handle_pic))

        return {
            'excelSize': len(response.content),
            'result': response.text,
            'shop_id': self.__shop_id,
            'platform': platform,
            'shop_name': shop_name,
            'shop_url': shop_url,
            'banner_imgs': banner_handle_pic,
            'update_time': update_time,
        }

    def result_hook(self, result, task):
        if self.__callback_link:
            self.crawl_handler_page(ShopCallback(self.__callback_link, priority=self.__priority))
            processor_logger.info("已请求回调链接：{}".format(self.__callback_link))
