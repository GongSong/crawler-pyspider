import locale
import random

import os
from PIL import Image
from selenium.webdriver import ActionChains

from alarm.page.ding_talk import DingTalk

locale.setlocale(locale.LC_ALL, 'C')

import time

from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class Jingdong:
    """
    京东商家后台的 cookie 获取;
    京东后台登录需要使用 service01 上的代理;
    """
    URL = 'https://sz.jd.com/productAnalysis/productDetail.html'
    # PROXY = '10.0.5.58:3128'
    PROXY = ''

    def __init__(self, username, password, proxy=None):
        """
        京东帐号
        :param url:
        :param username:
        :param password:
        """
        self.__url = self.URL
        self.__username = username
        self.__password = password
        self.__driver = Webdriver().set_proxy(proxy if proxy else self.PROXY).get_driver()
        self.__last_url = self.URL
        self.__platform = CookieData.CONST_PLATFORM_JINGDONG,
        self.__retry = 0

    def get_cookies_dict(self):
        """"
        以字典的方式返回cookie
        """
        if self.__retry > 5:
            print('重试次数到了: {} 次，退出并等待人工操作'.format(self.__retry))
            token = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
            title = '京东爬虫报警'
            content = '京东爬虫登录失败次数到了: {} 次，退出并等待人工操作'.format(self.__retry)
            DingTalk(token, title, content).enqueue()
        self.__driver.get(self.__url)
        self.__driver.fullscreen_window()
        time.sleep(5)

        # Enter account and password
        self.input_account_and_pwd()

        # 判断是否已经成功登录
        if self._successfully_logged():
            print('success login')
        else:
            self.__retry += 1
            print('failed login, stop 5s and retry, retry times: {}'.format(self.__retry))
            time.sleep(5)
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
        # 点击登录按钮进入登录页
        self.__driver.find_element_by_class_name('login-btn').click()
        time.sleep(2)
        # 转到登录的 iframe
        self.__driver.switch_to_frame('dialogIframe')
        time.sleep(1)
        # 点击账户登录按钮
        self.__driver.find_element_by_xpath('/html/body/div[2]/div[2]/a').click()
        # 输入用户名
        user_el = self.__driver.find_element_by_id('loginname')
        user_el.click()
        Webdriver.send_keys_slow(user_el, self.__username)
        # 输入密码
        pwd_el = self.__driver.find_element_by_id("nloginpwd")
        pwd_el.click()
        Webdriver.send_keys_slow(pwd_el, self.__password)
        # 点击登录
        submit_btn = self.__driver.find_element_by_id("loginsubmit").click()
        # self.__driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(5)
        # 滑动验证破解
        self.crack_slash_bar()

        time.sleep(100000)

    def crack_slash_bar(self):
        """
        破解滑动验证
        :return:
        """
        # 判断是否有滑动验证，有则进行滑动破解
        if not self.has_slash_bar():
            print('没有滑动验证，直接登录')
            return
        print('有滑动验证')
        time.sleep(2222)
        img_file = os.getcwd()

        # 图片元素地址
        img_element = self.__driver.find_element_by_xpath(
            '//*[@id="JDJRV-wrap-loginsubmit"]/div/div/div/div[1]/div[2]/div[1]/img')

        # 截图
        self.__driver.save_screenshot(img_file + '/image.png')
        print('window size', self.__driver.get_window_size())

        left = img_element.location['x']
        top = img_element.location['y']
        right = img_element.location['x'] + img_element.size['width']
        bottom = img_element.location['y'] + img_element.size['height']
        print('left: {}'.format(left))
        print('top: {}'.format(top))
        print('right: {}'.format(right))
        print('bottom: {}'.format(bottom))

        im = Image.open(img_file + '/image.png')
        im = im.crop((left, top, right, bottom))
        im.save(img_file + '/image_crop.png')
        Image.open(img_file + '/image_crop.png').show()

    def has_slash_bar(self):
        """
        判断是否有滑动验证码
        :return:
        """
        try:
            self.__driver.find_element_by_xpath('//*[@id="JDJRV-wrap-loginsubmit"]/div/div/div/div[2]/div[3]')
            return True
        except Exception as e:
            print('slash bar error msg: {}'.format(e))
            return False

    def random_click_webpage(self, el):
        """
        随机点击页面上的点，伪造人为痕迹
        :param el: 能够执行 click 方法的实例，比如 el = self.__driver.find_element_by_id('xx')
        :return:
        """
        action = ActionChains(self.__driver)
        window_size = self.__driver.get_window_size()
        width = window_size['width']
        height = window_size['height']
        print('width: {}'.format(width))
        print('height: {}'.format(height))
        for i in range(random.randint(3, 7)):
            random_width = random.randint(200, width - 200)
            random_height = random.randint(150, height - 150)
            print('random_width: {}'.format(random_width))
            print('random_height: {}'.format(random_height))
            action.move_to_element_with_offset(el, random_width, random_height).click().perform()
            time.sleep(random.randint(1, 3))
        submit_btn = self.__driver.find_element_by_id('loginsubmit')
        submit_width = submit_btn.size['width']
        submit_height = submit_btn.size['height']
        action.move_to_element_with_offset(submit_btn, random.randrange(submit_width),
                                           random.randrange(submit_height)).click().perform()

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
            self.__driver.find_element_by_class_name('menu')
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
