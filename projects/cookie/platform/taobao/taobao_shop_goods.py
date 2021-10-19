import json
import random
import time

from cookie.model.data import Data as CookieData
from cookie.config import *
from crawl_taobao_goods_migrate.model.result import Result
from crawl_taobao_goods_migrate.page.goods_details import GoodsDetails
from pyspider.libs.webdriver import Webdriver
from bs4 import BeautifulSoup


class TaobaoShopGoods:
    """
    用h5页面抓取淘宝店铺的商品内容
    """
    URL = 'https://shop{}.taobao.com/search.htm?search=y&orderType=newOn_desc'

    def __init__(self, shop_id_list):
        self.__driver = Webdriver().set_headless().get_driver()
        self.__driver.set_page_load_timeout(30)
        self.__page_nums = 0
        self.__current_page = 1
        self.__shop_crawled_status = False
        self.__shop_id_list = shop_id_list
        self.__url = None

    def catch_all_goods(self):
        for shop_id in self.__shop_id_list:
            # self.set_browser_cookie(shop_id)
            self.__page_nums = 0
            self.__current_page = 1
            self.__shop_crawled_status = self.shop_crawled_status(shop_id)
            self.__url = self.URL.format(shop_id)
            self.__driver.get(self.__url)
            time.sleep(5)
            print('开始抓取店铺：{} 的商品内容'.format(shop_id))

            # 递归抓取下一页
            self.catch_next_page(shop_id)

    def set_browser_cookie(self, shop_id):
        """
        设置淘宝店铺的cookies
        :param shop_id:
        :return:
        """
        self.__driver.get(self.URL.format(shop_id))
        cookies = json.loads(
            CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SHOP, CookieData.CONST_USER_TAOBAO_SHOP[0][0]))
        for _c in cookies:
            self.__driver.add_cookie(_c)

    def catch_next_page(self, shop_id):
        """
        判断是否有下一页
        :return:
        """
        try:
            print('抓取第: {} 页'.format(self.__current_page))
            result = self.__driver.page_source
            soup = BeautifulSoup(result, 'lxml')
            # 获取总页码
            if not self.__page_nums:
                self.__page_nums = int(soup.find('span', class_='page-info').get_text().split('/', 1)[1].strip())

            # 获取商品ID
            all_goods = soup.find_all('dl', class_='item')
            for _g in all_goods:
                goods_url = _g.find('a', class_='J_TGoldData')['href']
                goods_id = goods_url.split('id=', 1)[1].split('&', 1)[0]
                crawl_url = 'https://item.taobao.com/item.htm?id={}'.format(goods_id)
                print('解析商品: {}'.format(crawl_url))
                GoodsDetails(crawl_url).enqueue()

            if self.__shop_crawled_status and self.__current_page >= SHOP_CRAWLED_PAGES:
                print('全量抓取过的店铺，只抓取前: {} 页'.format(SHOP_CRAWLED_PAGES))
            else:
                self.__driver.find_element_by_css_selector("[class='J_SearchAsync next']").click()
                time.sleep(random.randint(5, 10))
                self.__current_page += 1
                self.catch_next_page(shop_id)

        except Exception as e:
            if self.__current_page < self.__page_nums or self.__current_page == 1:
                print('获取下一页失败: {}, 退出'.format(e))
            else:
                print('已到达最后一页第 {} 页，退出: {}'.format(self.__current_page, e))
                # 更改被抓取店铺的状态
                Result().update_shop_crawled_status(shop_id, True)
                print('已更改店铺的抓取状态')

    def shop_crawled_status(self, shop_id):
        """
        店铺是否已完整抓取的状态
        :return:
        """
        shop = Result().find_shop_by_id(shop_id)
        status = shop.get('result').get('crawled', False) if shop else False
        print('status: {}'.format(status))
        return status

    def __del__(self):
        """
        最后会销毁所有chrome进程
        :return:
        """
        try:
            self.__driver.close()
        except:
            pass
