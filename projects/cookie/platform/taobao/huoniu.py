import time

from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class Huoniu:
    """
    天猫火牛
    """
    URL = 'https://login.taobao.com/member/login.jhtml?f=top&sub=true&redirectURL=http%3A%2F%2Ffuwu.taobao.com%2Fusing%2Fserv_using.htm%3Fservice_code%3Dts-13280%26_j%3D4'
    # PROXY = '10.0.5.58:3128'
    PROXY = ''

    def __init__(self, username, password):
        self.__url = self.URL
        self.__username = username
        self.__password = password
        self.__driver = Webdriver().set_proxy(self.PROXY).get_driver()
        self.__last_token = ''
        self.__platform = CookieData.CONST_PLATFORM_TAOBAO_HUONIU

    def get_cookies_dict(self):
        """"
        以字典的方式返回cookie
        """
        self.__driver.get(self.__url)
        time.sleep(5)
        # 判断是否有二维码，有则点击二维码
        if self._check_qr_code():
            print('has qr_code')
            self.__driver.find_element_by_class_name('login-switch').click()
        else:
            print('no qr_code')
        # time.sleep(2)
        # 用户名的input框上面有个span，需要先点击这个span
        self.__driver.find_element_by_class_name("ph-label").click()
        # 输入用户名
        el = self.__driver.find_element_by_id("TPL_username_1")
        el.clear()
        Webdriver.send_keys_slow(el, self.__username)
        # 输入密码
        el = self.__driver.find_element_by_id("TPL_password_1")
        el.click()
        Webdriver.send_keys_slow(el, self.__password)
        time.sleep(5)
        # 点击登录
        self.__driver.find_element_by_id("J_SubmitStatic").click()
        time.sleep(10)
        # 判断是否已经成功登录
        if self._successfully_logged():
            print('success login')
        else:
            print('failed login, stop 60s')
            time.sleep(10)

        current_url = self.__driver.current_url
        self.__last_token = current_url.split('s=/Index/Index/index/tid/', 1)[1]
        last_url = 'https://mobile.kaquanbao.com/product/huoniu/rel/index.php?s=/Items/Index/index/tid/{}'.format(
            self.__last_token)
        if last_url:
            self.__driver.get(last_url)
            time.sleep(10)
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        return cookies_dict

    def get_cookies_str(self):
        """
        以字符串的方式返回cookie
        :return:
        """
        return "; ".join([str(x) + "=" + str(y) for x, y in self.get_cookies_dict().items()]) + ':token{}'.format(
            self.__last_token)

    def update_cookies(self):
        """
        更新cookies
        :return:
        """
        cookies = self.get_cookies_str()
        CookieData.set(self.__platform, self.__username, cookies)
        print(self.__driver.current_url)
        return cookies

    def _check_qr_code(self):
        """
        判断登录页是否有二维码
        :return:
        """
        try:
            self.__driver.find_element_by_class_name('ph-label').click()
            return False
        except Exception as e:
            print(e)
            return True

    def _successfully_logged(self):
        """
        根据某个标签判断页面是否已经正确登录
        :return:
        """
        try:
            self.__driver.find_element_by_class_name('NewNav')
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
