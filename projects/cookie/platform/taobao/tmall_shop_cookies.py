import time

from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class TmallShopCookies:
    """
    获取天猫店铺首页的cookies
    """

    def __init__(self, shop_url):
        self.__driver = Webdriver().get_driver()
        self.__driver.set_page_load_timeout(30)
        self.__url = shop_url

    def catch_page(self, retry=3):
        """
        判断是否有下一页
        :return:
        """
        try:
            print('抓取天猫店铺: {}, retry:{}'.format(self.__url, retry))
            self.__driver.get(self.__url)
            time.sleep(5)
            self.__driver.get(self.__url)
            if not self._successfully_logged:
                self.catch_page(retry - 1)
            self.get_cookies_str()
            self.__driver.quit()

        except Exception as e:
            print('shop error: {}'.format(e))
            if retry > 0:
                self.catch_page(retry - 1)

    def get_cookies_str(self):
        """
        以字符串的方式返回cookie
        保存cookie到redis
        :return:
        """
        # 获取cookie
        print("获取店铺的cookie")
        cookies = "; ".join([str(x) + "=" + str(y) for x, y in self.get_cookie().items()])
        print("cookies: {}".format(cookies))
        CookieData.sadd(CookieData.CONST_PLATFORM_TMALL_SHOP_GOODS, cookies)

    def get_cookie(self):
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        return cookies_dict

    def _successfully_logged(self, class_tag='slogo-shopname'):
        """
        根据某个标签判断页面是否已经正确登录
        :return:
        """
        print('开始验证是否成功登录')
        time.sleep(10)
        try:
            self.__driver.find_element_by_class_name(class_tag)
            return True
        except Exception as e:
            print('check successfully logged error msg: {}'.format(e))
            return False

    def __del__(self):
        """
        最后会销毁所有chrome进程
        :return:
        """
        try:
            self.__driver.close()
        except:
            pass
