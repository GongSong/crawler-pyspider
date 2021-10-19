import json

from bs4 import BeautifulSoup

from crawl_taobao_goods_migrate.model.task import Task
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from crawl_taobao_goods_migrate.config import *

from crawl_taobao_goods_migrate.page.goods_shelf_callback import GoodsShelfCallback


class GoodsShelf(BaseCrawl):
    """
    监控商品上下架类
    """

    IMAGE_NAME = 'goods_shelf'

    def __init__(self, goods_url, priority=0):
        super(GoodsShelf, self).__init__()
        self.__goods_url = goods_url
        self.__goods_id = goods_url.split('id=', 1)[1].split('&', 1)[0]
        self.__name = self.IMAGE_NAME
        self.__priority = priority

    def crawl_builder(self):
        builder = CrawlBuilder() \
                    .set_url(self.__goods_url) \
                    .set_headers_kv('User-Agent', USER_AGENT) \
                    .schedule_priority(self.__priority) \
                    .schedule_age() \
                    .set_task_id(Task.get_task_id_goods_shelf(self.__goods_id))

        return builder

    def parse_response(self, response, task):
        content = response.text
        real_url = response.url

        # 判断商品是否下架
        processor_logger.info('判断商品: {} 的上下架状态开始'.format(real_url))

        update_time = Date.now().format()
        off_shelf = False
        soup = BeautifulSoup(content, 'lxml')

        off_shelf_soup2 = soup.find('p', class_='tb-hint')
        if off_shelf_soup2:
            off_shelf = True

        off_shelf_soup1 = soup.find('div', class_='error-notice-hd')
        if off_shelf_soup1:
            off_shelf = True

        off_shelf_soup01 = soup.find('strong', class_='sold-out-tit')
        if off_shelf_soup01:
            off_shelf = True

        off_shelf_soup02 = soup.find('div', class_='error-notice-hd')
        off_shelf_soup03 = soup.find('div', class_='errorDetail')
        if off_shelf_soup02 or off_shelf_soup03:
            off_shelf = True

        # 商品类别，淘宝还是天猫......
        shop_type = 1 if 'taobao' in real_url else 2

        # 获取商品名
        goods_name = self.get_goods_name(soup, shop_type)

        # 获取商品的主图
        main_img = self.get_main_img(content, shop_type)

        # 获取商品的轮播图
        polling_img = self.get_polling_img(content, shop_type)

        # 更改已商品的下架状态
        return {
            'update_time': update_time,
            'off_shelf': off_shelf,
            'goods_name': goods_name,
            'main_img': main_img,
            'polling_img': polling_img,
            'shop_type': shop_type,
        }

    def result_hook(self, result, task):
        shop_type = result.get('shop_type')

        # 构造回调链接
        callback_link = 'http://ichuanyi.com/internal.php?method=thirdparty.fetchGoods&goodsId={}&platf' \
                        'orm={}&fetchType=1&force=0'.format(self.__goods_id, shop_type)
        self.crawl_handler_page(GoodsShelfCallback(callback_link, priority=self.__priority))
        processor_logger.info("已请求回调链接：{}".format(callback_link))


    def get_goods_name(self, soup, shop_type):
        """
        获取商品名称
        :param soup:
        :param shop_type:
        :return:
        """
        if shop_type == 1:
            goods_name_soup = soup.find('title')
            goods_name = goods_name_soup.get_text().strip().split('-', 1)[0] if goods_name_soup else ''
            return goods_name
        elif shop_type == 2:
            goods_name_soup = soup.find('meta', attrs={'name': 'keywords'})['content']
            goods_name = goods_name_soup.strip() if goods_name_soup else ''
            return goods_name
        else:
            return ''

    def get_main_img(self, content, shop_type):
        """
        获取商品主图
        :param content:
        :param shop_type:
        :return:
        """

        if shop_type == 1:
            try:
                main_img = 'https:' + content.split('pic              : \'', 1)[1].split('\',', 1)[0]
                if 'alicdn' not in main_img:
                    raise TypeError
            except Exception as e:
                processor_logger.error('未抓取到main img, error: {}'.format(e))
                main_img = ''
            return main_img
        elif shop_type == 2:
            try:
                main_img_soup = content.split('<img id="J_ImgBooth"', 1)[1].split('/>', 1)[0]
                main_img = 'https:' + main_img_soup.split('src="', 1)[1].split('.jpg')[0] + '.jpg'
            except Exception as e:
                processor_logger.warning('main_img 商品主图未获取到, error: {}'.format(e))
                main_img = ''
            return main_img
        else:
            return ''

    def get_polling_img(self, content, shop_type):
        """
        获取商品轮播图
        :param content:
        :param shop_type:
        :return:
        """
        if shop_type == 1:
            try:
                polling_img = content.split('auctionImages    : ', 1)[1].split('},', 1)[0].strip()
                img_list = []
                for img in json.loads(polling_img):
                    img_list.append('https:' + img)
                polling_img = img_list
            except Exception as e:
                processor_logger.error('未抓取到polling img, error: {}'.format(e))
                polling_img = ''
            return polling_img
        elif shop_type == 2:
            try:
                show_pages = content.split('<ul id="J_UlThumb"', 1)[1].split('</ul>', 1)[0]
                img_list = []
                show_pages_li = show_pages.split('<img src="')
                for img in show_pages_li:
                    if 'img.alicdn.com' in img:
                        img_list.append('https:' + img.split('.jpg', 1)[0] + '.jpg')
                polling_img = img_list
            except Exception as e:
                processor_logger.warning('没有轮播图 polling_img, error: {}'.format(e))
                polling_img = ''
            return polling_img
        else:
            return ''
