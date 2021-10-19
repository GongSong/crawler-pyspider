import json

from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData
import time
from lxml import etree
import re
import random
from pyspider.core.model.storage import default_storage_redis


class TmallProductPrice:
    URL = 'https://shop{}.taobao.com/search.htm?search=y&orderType=newOn_desc'
    KEY = "tmall_product_price"

    def __init__(self, shop_id_list):
        self.__driver = Webdriver().add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2}).get_driver()
        self.__driver.set_page_load_timeout(30)
        self.__page_nums = 0
        self.__current_page = 1
        self.__shop_crawled_status = False
        self.__shop_id_list = shop_id_list
        self.__url = None

    def set_browser_cookie(self, shop_id):
        """
        设置淘宝店铺的cookies
        :param shop_id:
        :return:
        """
        self.__driver.get(self.URL.format(shop_id))
        self.__driver.delete_all_cookies()
        cookie = CookieData.get(CookieData.CONST_PLATFORM_TMALL_PRODUCT, CookieData.CONST_USER_TMALL_PRODUCT[0][0])
        cookies = [cookie.strip() for cookie in cookie.split(';')]
        for _c in cookies:
            k, v = _c.split('=', 1)
            self.__driver.add_cookie({'name': k, 'value': v})

    def catch_all_goods(self):
        default_storage_redis.delete(self.KEY)
        for shop_id in self.__shop_id_list:
            self.set_browser_cookie(shop_id)
            self.__page_nums = 0
            self.__current_page = 1
            self.__url = self.URL.format(shop_id)
            self.__driver.get(self.__url)
            time.sleep(5)
            print('开始抓取店铺：{} 的商品内容'.format(shop_id))

            # 递归抓取下一页
            self.catch_next_page(shop_id)

    def catch_next_page(self, shop_id):
        """
        判断是否有下一页
        :return:
        """
        try:
            print('抓取第: {} 页'.format(self.__current_page))
            html = etree.HTML(self.__driver.page_source)

            all_goods = html.xpath('//div[@class="J_TItems"]/div/dl')
            for goods in all_goods:
                goods_url = goods.xpath('dd[@class="detail"]/a/@href')[0]
                goods_id = re.findall("id=(.*?)&",goods_url)[0]
                price = goods.xpath('dd[@class="detail"]//span[@class="c-price"]/text()')[0].strip()
                # goods_name = goods.xpath('dd[@class="detail"]/a/text()')[0].strip()
                comment = goods.xpath('dd[@class="rates"]')
                if comment:
                    item_str = json.dumps({goods_id:price})
                    default_storage_redis.sadd(self.KEY, item_str)
            self.__driver.find_element_by_css_selector("[class='J_SearchAsync next']").click()
            time.sleep(random.randint(5, 10))
            self.__current_page += 1
            self.catch_next_page(shop_id)


        except Exception as e:
            if self.__current_page < self.__page_nums or self.__current_page == 1:
                print('获取下一页失败: {}, 退出'.format(e))
            else:
                print('已到达最后一页第 {} 页，退出: {}'.format(self.__current_page, e))

    def __del__(self):
        """
        最后会销毁所有chrome进程
        :return:
        """
        try:
            self.__driver.close()
        except:
            pass

if __name__ == '__main__':
    TmallProductPrice(["479195376"]).catch_all_goods()