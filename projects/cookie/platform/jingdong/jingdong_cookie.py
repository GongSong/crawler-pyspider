import base64
import re
from selenium.webdriver import ActionChains

from cookie.config import JD_TRACE_POOL
from cookie.model.data import Data as CookieData
from pyspider.helper.date import Date, timestamp_to_str
from pyspider.libs.webdriver import Webdriver
import time
import cv2
import numpy as np
import random


class JingDongLogin:
    URL = 'https://sz.jd.com/productAnalysis/productDetail.html'
    PROXY = ''

    def __init__(self, username, password, proxy=None):
        self.__driver = Webdriver().set_proxy(proxy if proxy else self.PROXY).get_driver()
        self.__username = username
        self.__password = password
        self.__retry = 10

    def login(self):
        print('开始登录京东后台，用户名:{}'.format(self.__username))
        self.__driver.get(self.URL)
        self.__driver.set_window_size(1915, 1015)
        self.__driver.find_element_by_class_name('login-btn').click()
        time.sleep(2)
        # 转到登录的 iframe
        self.__driver.switch_to_frame('dialogIframe')
        time.sleep(2)
        # 点击账户登录按钮
        self.__driver.find_element_by_xpath('/html/body/div[2]/div[2]/a').click()
        # 输入用户名
        print('输入用户名')
        user_el = self.__driver.find_element_by_id('loginname')
        user_el.click()
        Webdriver.send_keys_slow(user_el, self.__username)
        # 输入密码
        print('输入密码')
        pwd_el = self.__driver.find_element_by_id("nloginpwd")
        pwd_el.click()
        Webdriver.send_keys_slow(pwd_el, self.__password)
        self.__driver.find_element_by_id("loginsubmit").click()
        time.sleep(8)

        return_cookie = ''
        if self._successfully_logged():
            return_cookie = self.get_cookies_str()
        else:
            self.crack_puzzle_captcha()
            if self._successfully_logged():
                return_cookie = self.get_cookies_str()

        self.__driver.close()
        return return_cookie

    def get_cookie(self):
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        return cookies_dict

    def get_cookies_str(self):
        """
        以字符串的方式返回cookie
        保存cookie到redis
        :return:
        """
        # 获取cookie
        cookies = "; ".join([str(x) + "=" + str(y) for x, y in self.get_cookie().items()])
        CookieData.set(CookieData.CONST_PLATFORM_JINGDONG, CookieData.CONST_USER_JINGDONG[0][0], cookies)
        return cookies

    def crack_puzzle_captcha(self):
        """
        破解滑块拼图验证码，失败则重试
        :return:
        """
        for i in range(self.__retry):
            try:
                print('第:{}次尝试破解'.format(i + 1))
                template_image = self.__driver. \
                    find_element_by_xpath("//div[@class='JDJRV-bigimg']/img") \
                    .get_attribute('src')
                target_image = self.__driver.find_element_by_xpath("//div[@class='JDJRV-smallimg']/img").get_attribute('src')
                time.sleep(2)
                self.translate_pic_code(template_image, 'template_image')
                self.translate_pic_code(target_image, 'target_image')
                time.sleep(2)
                distance = self.get_shadow_distance('template_image.jpg', 'target_image.jpg')
                self.crack_slide_bar(distance)
                time.sleep(3)
                if self._successfully_logged():
                    break
            except Exception as e:
                print("破解滑块拼图验证码失败,error:{}".format(e))
                time.sleep(2)
        time.sleep(3)

    def translate_pic_code(self, pic_code, save_name):
        result = re.search("base64,(?P<data>.*)", pic_code, re.DOTALL)
        data = result.groupdict().get("data")
        img = base64.urlsafe_b64decode(data)

        with open(save_name + '.jpg', "wb") as f:
            f.write(img)

    def get_shadow_distance(self, template_img, target_img):
        target = cv2.imread(target_img, 0)
        template = cv2.imread(template_img, 0)
        w, h = target.shape[::-1]
        temp = 'temp.jpg'
        targ = 'targ.jpg'
        cv2.imwrite(temp, template)
        cv2.imwrite(targ, target)
        target = cv2.imread(targ)
        # 转换为灰度
        target = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        target = abs(255 - target)
        cv2.imwrite(targ, target)
        target = cv2.imread(targ)
        template = cv2.imread(temp)
        result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
        x, y = np.unravel_index(result.argmax(), result.shape)
        # 展示圈出来的区域
        cv2.rectangle(template, (y, x), (y + w, x + h), (7, 249, 151), 2)
        # self.show_pic(template)
        x, y = np.unravel_index(result.argmax(), result.shape)
        print(x, y)
        return y

    def show_pic(self, name):
        cv2.imshow('Show', name)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def crack_slide_bar(self, distance):
        trace = random.choice(JD_TRACE_POOL)
        normalize_trace = distance / trace[-1][0] * 28 / 36
        print(normalize_trace)
        slider_bar = self.__driver.find_element_by_xpath("//div[@class='JDJRV-slide-inner JDJRV-slide-btn']")
        offset = []
        for i in range(1, len(trace)):
            x_offset = int(round((trace[i][0] - trace[i - 1][0]) * normalize_trace))
            y_offset = int(round((trace[i][1] - trace[i - 1][1]) * normalize_trace))
            offset.append((x_offset, y_offset))
        print(offset)
        action = ActionChains(self.__driver)
        action.click_and_hold(slider_bar)
        for x in offset:
            action.move_by_offset(xoffset=x[0], yoffset=x[1])
        time.sleep(0.5)
        action.release(slider_bar).perform()
        time.sleep(1)

    def _successfully_logged(self):
        """
        根据某个标签判断页面是否已经正确登录
        :return:
        """
        try:
            self.__driver.find_element_by_class_name('user-center')
            print('JD background account successfully logged in.')
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
            self.__driver.quit()
        except:
            pass


if __name__ == '__main__':
    JingDongLogin('icy-05', 'yourdream123').login()
