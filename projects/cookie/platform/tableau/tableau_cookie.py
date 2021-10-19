import time
from alarm.page.ding_talk import DingTalk
from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class TableauCookie:
    """
    tableau 的 cookie 获取;
    """
    URL = 'https://tableau.ichuanyi.com'
    PROXY = ''

    def __init__(self, username, password, proxy=None):
        """
        tableau帐号
        :param url:
        :param username:
        :param password:
        """
        self.__url = self.URL
        self.__username = username
        self.__password = password
        self.__driver = Webdriver().set_proxy(proxy if proxy else self.PROXY).get_driver()
        self.__last_url = None
        self.__platform = CookieData.CONST_PLATFORM_TABLEAU
        self.__retry = 0

    def get_cookies_dict(self):
        """"
        以字典的方式返回cookie
        """
        if self.__retry > 3:
            print('重试次数到了: {} 次，退出并等待人工操作'.format(self.__retry))
            token = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
            title = 'tableau登录报警'
            content = 'tableau登录失败次数到了: {} 次，退出并等待人工操作'.format(self.__retry)
            DingTalk(token, title, content).enqueue()
            return
        self.__driver.get(self.__url)
        time.sleep(5)

        # 登录输入、提交登录部分
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
        # 退出webdriver
        self.__driver.quit()
        return cookies_dict

    def input_account_and_pwd(self):
        """
        输入用户名，密码，以及点击登录
        :return:
        """
        # 输入用户名
        el = self.__driver.find_element_by_xpath(
            '//*[@id="ng-app"]/div/div/div/div[2]/span/form/div[1]/div[1]/div/div/input')
        el.clear()
        Webdriver.send_keys_slow(el, self.__username)
        # 输入密码
        el = self.__driver.find_element_by_xpath(
            '//*[@id="ng-app"]/div/div/div/div[2]/span/form/div[1]/div[2]/div/div/input')
        el.click()
        Webdriver.send_keys_slow(el, self.__password)
        time.sleep(2)
        # 点击登录
        self.__driver.find_element_by_xpath('//*[@id="ng-app"]/div/div/div/div[2]/span/form/button').click()
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
            self.__driver.find_element_by_class_name('ng-isolate-scope')
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
