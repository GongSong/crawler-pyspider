import time

from pyspider.helper.ips_pool import IpsPool
from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class TaobaoComment:
    """
    暂时没被用到
    """
    def __init__(self, goods_id, user_id):
        self.__driver = Webdriver().set_proxy(IpsPool().get_ip_from_pool()).get_driver()
        self.__driver.set_page_load_timeout(30)
        self.__goods_id = goods_id
        self.__user_id = user_id

    def update(self):
        self.__driver.get('https://item.taobao.com/item.htm?id={}'.format(self.__goods_id))
        # 暂停20s，手动扫描登录
        print('暂停20s，手动扫描登录')
        time.sleep(20)
        # self.__driver.find_element_by_id("sufei-dialog-close").click()
        self.__driver.find_element_by_xpath(
            u"(.//*[normalize-space(text()) and normalize-space(.)='宝贝详情'])[1]/following::a[1]").click()
        self.__driver.get(
            'https://rate.taobao.com/feedRateList.htm?auctionNumId={0}&userNumId={1}&currentPageNum={2}&pageSize=20'.format(
                self.__goods_id, self.__user_id, 2))
        time.sleep(5)
        cookies = Webdriver.get_cookies_str(self.__driver)
        CookieData.sadd(CookieData.CONST_PLATFORM_TAOBAO_COMMENT, cookies)
        CookieData.sexpire_del(CookieData.CONST_PLATFORM_TAOBAO_COMMENT)
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
