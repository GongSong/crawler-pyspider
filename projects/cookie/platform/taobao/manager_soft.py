import time

from backstage_data_migrate.page.manager_soft_export_log import ManagerSoftExLog
from cookie.config import *
from pyspider.helper.date import Date
from pyspider.libs.webdriver import Webdriver
from selenium.webdriver import ActionChains
from cookie.model.data import Data as CookieData


class ManagerSoft:
    """
    掌柜软件的批量导出宝贝数据cookie获取
    """
    URL = 'http://tb.maijsoft.cn/index.php?r=item/list'
    LAST_URL = 'http://tb.maijsoft.cn/index.php?r=export/index'
    # PROXY = '10.0.5.58:3128'
    PROXY = ''

    def __init__(self, username, password, channel):
        self.__url = self.URL
        self.__username = username
        self.__password = password
        self.__channel = channel
        self.__driver = Webdriver().set_proxy(self.PROXY).get_driver()
        self.__platform = CookieData.CONST_PLATFORM_TAOBAO_MANAGER_SOFT

    def get_cookies_dict(self):
        """"
        以字典的方式返回cookie
        """
        self.__driver.get(self.__url)
        time.sleep(5)
        # 点击授权登录
        self.__driver.find_element_by_xpath('//*[@id="page-bd"]/div[1]/a').click()
        time.sleep(2)
        # 判断是否有二维码，有则点击二维码
        if self._check_qr_code():
            print('has qr_code')
            # 切换iframe
            self.__driver.switch_to_frame(self.__driver.find_element_by_id('J_loginIframe'))
            time.sleep(1)
            switch_bar = self.__driver.find_element_by_class_name('login-switch')
            ActionChains(self.__driver).move_to_element(switch_bar).click().perform()
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
        time.sleep(5)
        # 判断是否已经成功登录
        if self._successfully_logged():
            print('success login')
        else:
            print('failed login, stop 10s')
            time.sleep(10)

        # 获取当前页面的cookies
        self.__driver.get(self.LAST_URL)
        time.sleep(1)
        cookies_str = self.get_cookies_str()
        CookieData.set(self.__platform, self.__username, cookies_str)
        print('cookies_str: {}'.format(cookies_str))
        time.sleep(1)
        # 筛选导出字段
        self.filter_words()
        # 勾选标签: 出售中的宝贝、仓库中的宝贝（所有等待上架的）,并导出
        self.mark_instock_goods()
        # 勾选标签: 仓库中的宝贝（所有仓库中的）,并导出
        self.mark_all_stock_goods()
        print('所有的导出完成')

        # 关闭本次抓取
        self.__driver.quit()

    def mark_all_stock_goods(self):
        """
        勾选标签：仓库中的宝贝（所有仓库中的）;
        导出之;
        :return:
        """
        retry = 0
        now = Date.now().format()
        compare_words = '所有仓库中的，导出字段：宝贝ID/淘宝类目/货号/商家编码'
        self.__driver.refresh()
        time.sleep(3)
        # 取消勾选出售中的宝贝
        print('取消勾选出售中的宝贝')
        self.__driver.find_element_by_xpath('//input[@id="J_itemStatusOnsale"]').click()
        time.sleep(3)
        # 切换到所有仓库中的宝贝标签
        print('勾选仓库中的宝贝')
        self.__driver.find_element_by_xpath('//input[@id="J_itemStatusInstock"]').click()
        time.sleep(3)
        print('勾选所有仓库中的商品')
        self.__driver.find_element_by_xpath('//option[@value="all_instock"]').click()
        time.sleep(3)
        # 导出所选项
        print('点击开始导出')
        export = self.__driver.find_element_by_xpath('//button[@id="J_startBtn"]')
        self.__driver.execute_script("arguments[0].click();", export)
        time.sleep(5)
        # 确认导出
        print('点击确认导出')
        export = self.__driver.find_element_by_xpath('//button[@class="sui-btn btn-primary btn-large"]')
        self.__driver.execute_script("arguments[0].click();", export)
        # 轮询确认是否已经拿到了本次导出的数据
        while True:
            result = self.get_export_log_result(now, compare_words)
            if result:
                print('找到了对应的导出数据')
                break
            else:
                print('未找到对应的导出数据')
                print('查看导出记录第: {}次, 暂停10s'.format(retry))
                time.sleep(10)
                if retry < MAX_ZG_WAIT_TIMES:
                    retry += 1
                else:
                    break

    def mark_instock_goods(self):
        """
        勾选标签：出售中的宝贝、仓库中的宝贝（所有等待上架的）;
        导出之;
        :return:
        """
        retry = 0
        now = Date.now().format()
        compare_words = '出售中的宝贝+所有等待上架的，导出字段：宝贝ID/淘宝类目/货号/商家编码'
        # 切换到所有仓库中的宝贝标签
        print('勾选仓库中的宝贝')
        self.__driver.find_element_by_xpath('//input[@id="J_itemStatusInstock"]').click()
        time.sleep(2)
        print('勾选所有等待上架的商品')
        self.__driver.find_element_by_xpath('//option[@value="for_shelved"]').click()
        time.sleep(2)
        # 导出所选项
        print('点击开始导出')
        export = self.__driver.find_element_by_xpath('//button[@id="J_startBtn"]')
        self.__driver.execute_script("arguments[0].click();", export)
        time.sleep(5)
        # 确认导出
        print('点击确认导出')
        export = self.__driver.find_element_by_xpath('//button[@class="sui-btn btn-primary btn-large"]')
        self.__driver.execute_script("arguments[0].click();", export)
        # 轮询确认是否已经拿到了本次导出的数据
        while True:
            result = self.get_export_log_result(now, compare_words)
            if result:
                print('找到了对应的导出数据')
                break
            else:
                print('未找到对应的导出数据')
                print('查看导出记录第: {}次, 暂停10s'.format(retry))
                time.sleep(10)
                if retry < MAX_ZG_WAIT_TIMES:
                    retry += 1
                else:
                    break

    def get_export_log_result(self, compare_time, compare_words, retry=3):
        """
        查询导出数据
        :return:
        """
        try:
            return ManagerSoftExLog(self.__username, compare_time, compare_words, self.__channel).get_result()
        except Exception as e:
            print('查询导出数据 error : {}'.format(e))
            if retry > 0:
                return self.get_export_log_result(compare_time, compare_words, retry - 1)
            return False

    def filter_words(self):
        """
        筛选导出字段,保留宝贝、淘宝类目、货号、商家编码
        :return:
        """
        self.__driver.get(self.LAST_URL)
        # -----------------------出售中的宝贝部分-------------------------------
        # 筛选标签
        time.sleep(2)
        print('取消标签')
        title = self.__driver.find_element_by_xpath('//span[text()="标题"]')
        self.__driver.execute_script("arguments[0].click();", title)
        time.sleep(2)
        price = self.__driver.find_element_by_xpath('//span[text()="价格"]')
        self.__driver.execute_script("arguments[0].click();", price)
        time.sleep(2)
        stock = self.__driver.find_element_by_xpath('//span[text()="库存"]')
        self.__driver.execute_script("arguments[0].click();", stock)
        time.sleep(2)
        # status = self.__driver.find_element_by_xpath('//span[text()="宝贝状态"]')
        # self.__driver.execute_script("arguments[0].click();", status)
        print('选中标签')
        time.sleep(2)
        taobao_category = self.__driver.find_element_by_xpath('//span[text()="淘宝类目"]')
        self.__driver.execute_script("arguments[0].click();", taobao_category)
        time.sleep(2)
        barcode = self.__driver.find_element_by_xpath('//span[text()="货号"]')
        self.__driver.execute_script("arguments[0].click();", barcode)
        time.sleep(2)

    def get_cookies_str(self):
        """
        以字符串的方式返回cookie
        :return:
        """
        cookies_dict = {}
        for _ in self.__driver.get_cookies():
            cookies_dict.setdefault(_['name'], _['value'])
        return "; ".join([str(x) + "=" + str(y) for x, y in cookies_dict.items()])

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
            self.__driver.find_element_by_class_name('main-nav-name ')
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
