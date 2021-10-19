from alarm.page.ding_talk import DingTalk

import time

from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class RedbookBloggerLive:
    """
    小红书博主直播数据的后台
    """
    URL = 'https://influencer.xiaohongshu.com/'
    PROXY = '10.0.5.58:3128'

    def __init__(self, username, password, proxy=None):
        """
        小红书帐号
        :param url:
        :param username:
        :param password:
        """
        self.__url = self.URL
        self.__username = username
        self.__password = password
        self.__driver = Webdriver().get_driver()  # .set_proxy(proxy if proxy else self.PROXY)
        self.__last_url = self.URL
        self.__platform = CookieData.CONST_PLATFORM_REDBOOK
        self.__retry = 0

    def get_cookies_dict(self):
        """"
        以字典的方式返回cookie
        """
        if self.__retry > 5:
            print('重试次数到了: {} 次，退出并等待人工操作'.format(self.__retry))
            token = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
            title = '小红书爬虫报警'
            content = '小红书爬虫登录失败次数到了: {} 次，退出并等待人工操作'.format(self.__retry)
            DingTalk(token, title, content).enqueue()
            return
        self.__driver.get(self.__url)
        time.sleep(5)

        # Enter account and password
        self.input_account_and_pwd()

        # 判断是否已经成功登录
        if self._successfully_logged():
            print('success login')
        else:
            self.__retry += 1
            print('failed login, stop 5s and retry, retry times: {}'.format(self.__retry))
            time.sleep(10)
            return self.get_cookies_dict()
        if self.__last_url:
            self.__driver.get(self.__last_url)
            time.sleep(5)
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        return cookies_dict

    def input_account_and_pwd(self):
        """
        输入用户名，密码，以及点击登录
        :return:
        """
        # print('\n', self.__driver.page_source, '\n')
        self.__driver.find_elements_by_class_name('login-big-button')[1].click()
        time.sleep(2)
        self.__driver.find_element_by_xpath('//div[@class="solar-login_header"]/div[2]').click()
        time.sleep(2)
        # 输入用户名
        el = self.__driver.find_element_by_xpath('//input[@placeholder="邮箱"]')
        el.clear()
        Webdriver.send_keys_slow(el, self.__username)
        # 输入密码
        pw = self.__driver.find_element_by_xpath('//input[@placeholder="密码"]')
        pw.click()
        Webdriver.send_keys_slow(pw, self.__password)
        time.sleep(2)
        # 点击登录
        self.__driver.find_elements_by_class_name("corona-button_pebble")[1].click()
        time.sleep(10)

    def get_cookies_str(self):
        """
        以字符串的方式返回cookie
        :return:
        """
        return "; ".join([str(x) + "=" + str(y) for x, y in self.get_cookies_dict().items()])

    def update_cookies(self):
        """
        更新cookies
        :return:
        """
        cookies = self.get_cookies_str()
        CookieData.set(self.__platform, self.__username, cookies)
        return cookies

    def _successfully_logged(self):
        """
        根据某个标签判断页面是否已经正确登录
        :return:
        """
        try:
            self.__driver.find_element_by_class_name('page-list_header')
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
