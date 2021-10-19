from cookie.platform.taobao.login_base import *


class TmallLogin(LoginBase):
    URL = "https://login.tmall.com"
    last_url = "https://icynz.tmall.com/search.htm?spm=a1z10.3-b-s.w4011-21240384224.380.4fa640fdwCHnay&search=y&user_number_id=3165080793&rn=75d14e09a31bb5f374675aac31a909ad&keyword=icy&pageNo=20&tsearch=y#anchor"

    def __init__(self, username, password):
        super(TmallLogin, self).__init__(self.URL, username, password, CookieData.CONST_PLATFORM_TMALL_PRODUCT)
        self.set_last_url(self.last_url)

    def login_operation(self, retry=3):
        """
        登录模块，专注账号密码输入、登录按钮点击、以及滑动验证码破解
        :return:
        """
        # 直接解析不到账号、密码输入框等元素，需要转到loginIframe里。
        try:
            # self.__driver为私有，需强行指定类名才能访问
            self._LoginBase__driver.switch_to.frame("J_loginIframe")
        except Exception as e:
            pass

        # 输入用户名
        el = self._LoginBase__driver.find_element_by_id("fm-login-id")
        el.clear()
        Webdriver.send_keys_slow(el, self._LoginBase__username)
        # 输入密码
        el = self._LoginBase__driver.find_element_by_id("fm-login-password")
        el.click()
        Webdriver.send_keys_slow(el, self._LoginBase__password)
        time.sleep(2)
        # 判断是否有滑动验证码
        self._check_slide_bar()
        time.sleep(2)
        # 点击登录
        self._LoginBase__driver.find_element_by_class_name("fm-submit").click()
        time.sleep(5)


if __name__ == '__main__':
    for account, password in CookieData.CONST_USER_TMALL_PRODUCT:
        TmallLogin(account, password).update_cookies()
