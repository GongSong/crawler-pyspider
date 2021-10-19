import os
import time
import zipfile

import redis

from backstage_data_migrate.config import REDIS_HOST, REDIS_PORT, REDIS_DB_ID
from pyspider.libs.oss import oss
from pyspider.libs.utils import md5string
from pyspider.libs.webdriver import Webdriver
from cookie.model.data import Data as CookieData
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class JDGoodsDetailsDl:
    """
    京东商品明细表格下载
    """
    URL = 'https://sz.jd.com/sz/view/productAnalysis/productDetails.html'
    PAUSE_TIME = 2

    def __init__(self):
        super(JDGoodsDetailsDl, self).__init__()
        self.__redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_ID)
        self.__driver = Webdriver().get_driver()
        self.__cookie = CookieData.get(CookieData.CONST_PLATFORM_JINGDONG, CookieData.CONST_USER_JINGDONG[0][0])

    def action(self):
        """
        表格下载入口
        :return:
        """
        self.__driver.get(self.URL)
        time.sleep(self.PAUSE_TIME)

        # 添加cookie登录
        self.use_cookie_login()
        # 去下载页
        self.__driver.get(self.URL)
        # 下载文件
        self.download_file()
        # 找到刚下载的京东商品明细表格，解压缩并保存
        self.save_jd_file()

    def use_cookie_login(self):
        """
        用cookie登录
        :return:
        """
        print('用cookie登录')
        my_cookies = [item.strip().split('=', 1) for item in self.__cookie.split(';')]
        for _cookie in my_cookies:
            self.__driver.add_cookie({'name': _cookie[0], 'value': _cookie[1]})

    def download_file(self, retry=3):
        """
        下载文件
        :return:
        """
        print('下载京东表格')
        delay_time = 10  # 等10s直到元素出现
        try:
            download_xpath = '//div[@class="fr grace-download-btn dl-warp ng-isolate-scope"]'
            WebDriverWait(self.__driver, delay_time).until(EC.presence_of_element_located((By.XPATH, download_xpath)))
            print('找到了下载按钮，点击下载')
            self.__driver.find_element_by_xpath(download_xpath).click()
            print('京东表格下载完成')
        except Exception as e:
            print('下载京东表格error:{}'.format(e))
            if retry > 0:
                time.sleep(self.PAUSE_TIME)
                print('下载京东表格重试剩余次数:{}'.format(retry - 1))
                return self.download_file(retry - 1)
            else:
                raise '下载京东表格失败,重试剩余次数:{}'.format(retry - 1)
        time.sleep(5)

    def save_jd_file(self):
        """
        找到刚下载的京东商品明细表格，解压缩并保存
        :return:
        """
        print('寻找刚下载的京东商品明细表格')
        jd_file_path = '../../pyspider/projects/logs'
        for root, dirs, files in os.walk(jd_file_path):
            for file_name in files:
                if '全部渠道_商品明细.zip' in file_name:
                    # 解压缩
                    with zipfile.ZipFile('{}/{}'.format(jd_file_path, file_name), 'r') as zip_ref:
                        zip_ref.extractall(jd_file_path)

        print('查找解压后的京东表格')
        for root, dirs, files in os.walk(jd_file_path):
            for file_name in files:
                if '全部渠道_商品明细.xls' in file_name:
                    # 保存到redis
                    print('保存京东表格:{}到数据库'.format(file_name))
                    with open('{}/{}'.format(jd_file_path, file_name), 'rb') as my_file:
                        # 保存到redis
                        print('保存到redis')
                        self.__redis.rpush("jingdong:{}".format(file_name.split('_')[1]), my_file.read())
                        # 保存到oss
                        print('保存到oss')
                        oss.upload_data(oss.get_key(oss.CONST_JD_GOODS_PATH, file_name), my_file.read())

        print('开始删除已上传的京东表格')
        for root, dirs, files in os.walk(jd_file_path):
            for file_name in files:
                if '全部渠道_商品明细' in file_name:
                    os.remove('{}/{}'.format(jd_file_path, file_name))
        print('删除已上传的京东表格完成')

    def __del__(self):
        self.__driver.quit()


if __name__ == '__main__':
    JDGoodsDetailsDl().action()
