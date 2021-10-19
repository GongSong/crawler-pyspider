import time

import random
from selenium import webdriver
from pyspider.config import config


class Webdriver:
    """
    webdriver的封装
    """
    def __init__(self):
        self.__chromedriver_path = 'bin/chromedriver'
        self.__chrome_options = webdriver.ChromeOptions()
        self.__chrome_options.add_argument('disable-infobars')
        self.__chrome_options.add_experimental_option('prefs', {
            'download.default_directory': config.get('log', 'log_dir'),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        })
        self.__driver = None

    def add_argument(self, argument):
        """
        chrome options 的 add_argument
        :param argument:
        :return:
        """
        self.__chrome_options.add_argument(argument)
        return self

    def add_experimental_option(self, name, value):
        """
        chrome options 的 add_experimental_option
        :param name:
        :param value:
        :return:
        """
        self.__chrome_options.add_experimental_option(name, value)
        return self

    def add_extension(self, extension):
        """
        添加扩展
        :param extension:
        :return:
        """
        self.__chrome_options.add_extension(extension)
        return self

    def set_proxy(self, proxy):
        """
        设置代理
        :param proxy:
        :return:
        """
        if proxy:
            self.__chrome_options.add_argument('--proxy-server=%s' % proxy)
        return self

    def set_headless(self):
        """
        设置无头
        :return:
        """
        # self.__chrome_options.headless = True
        self.__chrome_options.add_argument('--headless')
        return self

    def get_driver(self):
        """
        获取driver
        :return:
        """
        if not self.__driver:
            self.__driver = webdriver.Chrome(options=self.__chrome_options, executable_path=self.__chromedriver_path)
        return self.__driver

    @staticmethod
    def send_keys_slow(element, string):
        for _ in string:
            time.sleep(random.randrange(10, 100) * 0.0051)
            element.send_keys(_)

    @staticmethod
    def get_cookies_dict(driver):
        cookies_dict = {}
        for _ in driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        return cookies_dict

    @staticmethod
    def get_cookies_str(driver):
        return "; ".join([str(x) + "=" + str(y) for x, y in Webdriver.get_cookies_dict(driver).items()])
