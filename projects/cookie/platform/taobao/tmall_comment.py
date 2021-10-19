import time

from pyspider.helper.ips_pool import IpsPool
from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class TmallComment:
    def __init__(self, goods_id, user_id):
        self.__driver = Webdriver().get_driver()
        self.__driver.set_page_load_timeout(30)
        self.__goods_id = goods_id
        self.__user_id = user_id

    def update(self):
        self.__driver.get('https://detail.tmall.com/item.htm?id={}'.format(self.__goods_id))
        # 暂停60s，手动扫描登录
        print('暂停60s，手动扫描登录')
        time.sleep(60)
        # self.__driver.find_element_by_id("sufei-dialog-close").click()
        # self.__driver.find_element_by_xpath(
        #     u"(//*[@id='J_TabBar']/li[1]/a").click()
        self.__driver.get(
            'https://rate.tmall.com/list_detail_rate.htm?itemId={0}&sellerId={1}&currentPage={2}'.format(
                self.__goods_id, self.__user_id, 2))
        time.sleep(10)
        cookies = Webdriver.get_cookies_str(self.__driver)
        CookieData.sadd(CookieData.CONST_PLATFORM_TMALL_COMMENT, cookies)
        CookieData.sexpire_del(CookieData.CONST_PLATFORM_TMALL_COMMENT)
        return cookies

    def __del__(self):
        """
        最后会销毁所有chrome进程
        :return:
        """
        try:
            self.__driver.close()
        except:
            pass
