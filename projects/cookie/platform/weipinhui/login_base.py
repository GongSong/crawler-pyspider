import locale

from alarm.page.ding_talk import DingTalk
from cookie.config import DRIVER_PAGE_LOAD_TIME_OUT
from pyspider.core.model.storage import default_storage_redis

locale.setlocale(locale.LC_ALL, 'C')

import time
import os
import requests
import tesserocr

from PIL import ImageEnhance, Image

from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData


class LoginBase:
    def __init__(self, url, username, password, platform, proxy=None):
        """
        唯品会帐号基类
        :param url:
        :param username:
        :param password:
        """
        self.__url = url
        self.__username = username
        self.__password = password
        self.__driver = Webdriver().set_proxy(proxy).get_driver()
        self.__driver.set_page_load_timeout(DRIVER_PAGE_LOAD_TIME_OUT)
        self.__last_url = ''
        self.__platform = platform
        self.__retry = 0

    def set_last_url(self, url):
        """
        如果有值，登录完成后会进这个页面拿cookie
        :param url:
        :return:
        """
        self.__last_url = url
        return self

    def get_cookies_dict(self):
        """"
        以字典的方式返回cookie
        """
        if self.__retry > 8:
            print('重试次数到: {} 次，退出并等待人工操作'.format(self.__retry))
            token = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
            title = '唯品会爬虫报警'
            content = '唯品会爬虫登录失败次数到了: {} 次，退出并等待人工操作'.format(self.__retry)
            DingTalk(token, title, content).enqueue()
            return {
                'msg': '唯品会爬虫登录失败次数到了: {} 次，退出并等待人工操作'.format(self.__retry)
            }
        self.__driver.get(self.__url)
        time.sleep(5)
        # 判断是否已经成功登录
        if self._successfully_logged():
            print('success login')
            cookies_dict = {}
            for _ in self.__driver.get_cookies():
                cookies_dict.setdefault(_['name'], _['value'])
            return cookies_dict
        headers = {
            'Cookie': self.get_unlogined_cookie_str(),
        }
        # time.sleep(2)
        # 输入用户名
        el = self.__driver.find_element_by_id("userName")
        el.clear()
        Webdriver.send_keys_slow(el, self.__username)
        # 输入密码
        el = self.__driver.find_element_by_id("passWord")
        el.click()
        Webdriver.send_keys_slow(el, self.__password)
        time.sleep(2)
        # 输入验证码
        el = self.__driver.find_element_by_id("checkWord")
        el.click()
        check_word = self.get_check_word(headers)
        Webdriver.send_keys_slow(el, check_word)
        time.sleep(2)
        # 点击登录
        self.__driver.find_element_by_id("subMit").click()
        time.sleep(5)

        # 判断是否已经成功登录
        if self._successfully_logged():
            print('success login')
        else:
            self.__retry += 1
            print('failed login, stop 5s and retry, retry times: {}'.format(self.__retry))
            try:
                self.__driver.switch_to_alert().accept()
            except Exception as e:
                token = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
                title = '唯品会爬虫报警'
                content = '唯品会爬虫登录需要验证码，退出并等待人工操作'
                print(content)
                DingTalk(token, title, content).enqueue()
                raise e
            time.sleep(5)
            return self.get_cookies_dict()
        try:
            href = self.__driver.find_element_by_xpath("//nav[@class='menu-tree portal']/ul/li[5]/ul[1]/li[1]/ul[@class='menu-level2']/li[1]/a").get_attribute('href')
            default_storage_redis.set("vip_product_url", href)
            print(href)
        except:
            pass
        if self.__last_url:
            self.__driver.get(self.__last_url)
            time.sleep(5)
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        # 关闭本次的浏览器
        self.__driver.quit()
        return cookies_dict

    def get_unlogined_cookie_str(self):
        """
        返回登录之前的 cookie
        :return:
        """
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        return "; ".join([str(x) + "=" + str(y) for x, y in cookies_dict.items()])

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

    def get_check_word(self, headers):
        """
        解析图片验证码
        Mac 下的 tesserocr 安装步骤：
        1，brew install imagemagick
        2，brew install tesseract
        3，pip3 install tesserocr pillow
        :return:
        """
        img_url = 'https://vis.vip.com/checkCode.php'
        image = requests.get(img_url, headers=headers).content
        text = self.handle_img(image)

        if len(text) != 4:
            # 错误识别结果，继续重试
            return self.get_check_word(headers)
        else:
            return text

    def handle_img(self, image):
        """
        图像识别，传入一张图片，然后处理完，返回识别后的 text
        :param image:
        :return:
        """
        path = os.getcwd() + '/image.jpg'
        with open(path, 'wb') as file:
            file.write(image)
            print('已保存图片，地址为: {}'.format(path))
        img = Image.open(path)

        # 对比度增强
        enh_con = ImageEnhance.Contrast(img)
        contrast = 1.5
        image_contrasted = enh_con.enhance(contrast)

        # 锐度增强
        enh_sha = ImageEnhance.Sharpness(image_contrasted)
        sharpness = 2.5
        image_sharped = enh_sha.enhance(sharpness)

        # 放大图片
        enh_size = image_sharped.resize((704, 244))

        # 灰度和二值化
        img = enh_size.convert('L')
        threshold = 127
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)
        img = img.point(table, '1')
        img = self.clean_img(img, 3)

        text = tesserocr.image_to_text(img).strip()
        print('图片内容为: ({})'.format(text))

        if os.path.exists(path):
            os.remove(path)

        return text

    def clean_img(self, img, threshold):
        """
        图片降噪
        :param threshold:
        :return:
        """
        width, height = img.size
        for j in range(height):
            for i in range(width):
                point = img.getpixel((i, j))
                if point == 0:
                    for x in range(threshold):
                        if j + x >= height:
                            break
                        else:
                            if point != img.getpixel((i, j + x)):
                                img.putpixel((i, j), 1)
                                break
        return img

    def _successfully_logged(self):
        """
        根据某个标签判断页面是否已经正确登录
        :return:
        """
        try:
            main_url = 'http://vis.vip.com/index.php#/app-i/iframe-vue/app-v/vis-vue/index?t=1555314054867'
            self.__driver.get(main_url)
            time.sleep(1)
            self.__driver.find_element_by_class_name('menu-level0')
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
