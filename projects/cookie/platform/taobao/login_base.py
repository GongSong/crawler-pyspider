import time

from pyspider.helper.slide_captcha_crack import TmallSlideCaptchaCrack
from pyspider.libs.webdriver import Webdriver
from selenium.webdriver.common.alert import Alert
from pyspider.config import config
from cookie.model.data import Data as CookieData


class LoginBase:
    def __init__(self, url, username, password, platform, proxy=None):
        """
        淘系帐号基类
        :param url:
        :param username:
        :param password:
        """
        self.__url = url
        self.__username = username
        self.__password = password
        self.__driver = Webdriver().set_proxy(config.get('fixed_proxy', 'taobao') if not proxy else proxy).get_driver()
        self.__last_url = ''
        self.__platform = platform
        self.__class_tag = ''

    def set_last_url(self, url):
        """
        如果有值，登录完成后会进这个页面拿cookie
        :param url:
        :return:
        """
        self.__last_url = url
        return self

    def set_check_class_tag(self, class_tag):
        """
        设置检测是否成功登录的class 标签
        :param class_tag:
        :return:
        """
        self.__class_tag = class_tag
        return self

    def get_cookies_dict(self):
        """"
        以字典的方式返回cookie
        """
        self.__driver.get(self.__url)
        time.sleep(5)
        # 登录
        self.login_operation()

        if self.__last_url:
            self.__driver.get(self.__last_url)
            time.sleep(5)
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        # 关闭本次的浏览器
        self.__driver.quit()
        return cookies_dict

    def login_operation(self, retry=3):
        """
        登录模块，专注账号密码输入、登录按钮点击、以及滑动验证码破解
        :return:
        """
        # 判断是否有二维码，有则点击二维码
        if self._check_qr_code():
            print('has qr_code')
            try:
                self.__driver.find_element_by_class_name('login-switch').click()
            except Exception as e:
                print('没有二维码: {}'.format(e))
        else:
            print('no qr_code')
        # 用户名的input框上面有个span，需要先点击这个span
        try:
            self.__driver.find_element_by_class_name("ph-label").click()
        except Exception as e:
            print('没有找到用户名的input框上面的span标签: {}'.format(e))
        try:
            # 输入用户名
            el = self.__driver.find_element_by_id("TPL_username_1")
            el.clear()
            Webdriver.send_keys_slow(el, self.__username)
            # 输入密码
            el = self.__driver.find_element_by_id("TPL_password_1")
            el.click()
            Webdriver.send_keys_slow(el, self.__password)
            time.sleep(2)
            # 判断是否有滑动验证码
            self._check_slide_bar()
            time.sleep(2)
            # 点击登录
            self.__driver.find_element_by_id("J_SubmitStatic").click()
            time.sleep(3)
        except Exception as e:
            print("更换登录的锚定标签:{}".format(e))
            # 输入用户名
            el = self.__driver.find_element_by_id("fm-login-id")
            el.clear()
            Webdriver.send_keys_slow(el, self.__username)
            # 输入密码
            el = self.__driver.find_element_by_id("fm-login-password")
            el.click()
            Webdriver.send_keys_slow(el, self.__password)
            time.sleep(2)
            # 判断是否有滑动验证码
            self._check_slide_bar()
            time.sleep(2)
            # 点击登录
            self.__driver.find_element_by_class_name("fm-submit").click()
            time.sleep(3)

        # 判断是否已经成功登录
        if self._successfully_logged("app"):
            print('success login')
        else:
            if retry > 0:
                print('登录失败，再次重试，剩余重试次数:{}'.format(retry - 1))
                return self.login_operation(retry - 1)
            else:
                print('登录失败重试次数:{}次,暂停30s继续'.format(retry))
                time.sleep(30)

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

    def _check_slide_bar(self, retry=3):
        """
        判断是否有滑动验证码
        :return:
        """
        # 开始判断是否有滑动验证码，有则滑动破解
        if TmallSlideCaptchaCrack.check_slide_bar(self.__driver, id_element='nc_1_n1z'):
            if TmallSlideCaptchaCrack.crack_slide_bar(self.__driver, id_element='nc_1_n1z'):
                print('滑动破解成功，继续下一步')
            else:
                if retry > 0:
                    print('滑动破解失败，剩余重试次数: {}'.format(retry))
                    time.sleep(3)
                    return self._check_slide_bar(retry - 1)
                else:
                    print('滑动破解失败，剩余重试次数: {}'.format(retry))

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
            err_msg = e.args[0]
            print('err_msg', err_msg)
            if "您的浏览器限制了第三方Cookie" in err_msg:
                Alert(self.__driver).accept()
                time.sleep(2)
                self.__driver.refresh()
                time.sleep(2)
                print("出现提示：您的浏览器限制了第三方Cookie；已解除限制.")
                return False
            return True

    def _successfully_logged(self, check_id_tag='ceiling-nav'):
        """
        根据某个标签判断页面是否已经正确登录
        :return:
        """
        print('开始验证是否成功登录')
        time.sleep(20)
        try:
            if self.__class_tag:
                self.__driver.find_element_by_class_name(self.__class_tag)
            else:
                self.__driver.find_element_by_id(check_id_tag)
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
