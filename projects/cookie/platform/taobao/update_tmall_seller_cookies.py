import traceback

from bs4 import BeautifulSoup

from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.model.es.tmall_seller_order import TmallSellerOrderEs
from cookie.config import ROBOT_TOKEN
from cookie.platform.taobao.login_base import *
from pyspider.helper.date import Date


class TmallSeller:
    """
    生意参谋天猫渠道的cookie获取；
    目前有以下几个页面的数据：
    1, 商家中心: https://trade.taobao.com/trade/itemlist/list_sold_items.htm
    """
    URL = 'https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Ftrade.taobao.com%2Ftrade%2Fitemlist%2Flist_sold_items.htm'
    # PROXY = '10.0.5.58:3128'
    PROXY = ''

    def __init__(self, username, password, start_page, end_page, catch_all):
        """
        生意参谋天猫渠道的cookie获取
        :param url:
        :param username:
        :param password:
        :param start_page:
        :param end_page:
        :param catch_all:
        """
        self.__url = self.URL
        self.__username = username
        self.__password = password
        self.__start_page = start_page
        self.__end_page = int(end_page)
        self.__catch_all = catch_all
        self.__driver = Webdriver().set_proxy(
            config.get('fixed_proxy', 'taobao') if not self.PROXY else self.PROXY).get_driver()
        self.__last_url = 'https://trade.taobao.com/trade/itemlist/list_sold_items.htm'
        self.__page = 1

    def start_login(self):
        """
        登录sycm的入口
        :return:
        """
        self.login_entry()

    def login_entry(self):
        """"
        登录入口
        """
        self.__driver.get(self.__url)
        time.sleep(5)
        # 登录
        self.login_operation()

        if self.__last_url:
            self.__driver.get(self.__last_url)
            time.sleep(5)

        # 获取当页的数据
        self.catch_each_page()
        # 点击进入下一页
        for _page in range(self.__start_page, self.__end_page + 1):
            self.to_next_page()
        # 关闭本次的浏览器
        self.__driver.quit()

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
        # 输入用户名
        el = self.__driver.find_element_by_id("TPL_username_1")
        el.clear()
        Webdriver.send_keys_slow(el, self.__username)
        # 输入密码
        el = self.__driver.find_element_by_id("TPL_password_1")
        el.click()
        Webdriver.send_keys_slow(el, self.__password)
        time.sleep(5)
        # 判断是否有滑动验证码
        self._check_slide_bar()
        time.sleep(3)
        # 点击登录
        self.__driver.find_element_by_id("J_SubmitStatic").click()
        time.sleep(5)

        # 判断是否已经成功登录
        if self._successfully_logged():
            print('success login')
        else:
            if retry > 0:
                print('登录失败，再次重试，剩余重试次数:{}'.format(retry - 1))
                return self.login_operation(retry - 1)
            else:
                print('登录失败重试次数:{}次,暂停30s继续'.format(retry))
                time.sleep(30)

    def catch_each_page(self):
        """
        获取每页的详细订单商品数据
        :return:
        """
        try:
            print('解析第: {} 页的数据'.format(self.__page))
            soup = BeautifulSoup(self.__driver.page_source, 'lxml')
            # 每个订单级别的所有信息
            items = soup.find_all('div', class_='trade-order-main')
            sync_time = Date.now().format_es_utc_with_tz()
            save_list = []
            last_goods_code = ''
            last_order_id = ''
            for _item in items:
                # 订单信息那一列
                order_list = _item.find('table', class_='item-mod__head___38O6X')
                order_id_label = order_list.find('label', class_='item-mod__checkbox-label___cRGUj').find_all('span')
                order_id = order_id_label[2].get_text().strip()
                last_order_id = order_id
                order_create_time = Date(order_id_label[5].get_text().strip()).format_es_utc_with_tz()
                # 商品信息那一列
                goods_list = _item.find('table', class_='suborder-mod__order-table___2SEhF')
                goods_td = goods_list.find_all('tr', class_='suborder-mod__item___dY2q5')
                for td in goods_td:
                    save_dict = {}
                    _td = td.find('td')
                    p_items = _td.find_all('p')
                    # 跳过优惠券
                    if len(p_items) <= 3:
                        continue
                    # 拿到goods code
                    goods_code = p_items[3].find_all('span')[1].get_text().strip()
                    last_goods_code = goods_code
                    delivery_time = ''
                    # 获取发货时间
                    if len(p_items) > 4:
                        delivery_time = p_items[4].find_all('span')[1].get_text().strip()
                    save_dict['order_id'] = order_id
                    save_dict['goods_code'] = goods_code
                    save_dict['order_create_time'] = order_create_time
                    save_dict['delivery_time'] = delivery_time
                    save_dict['sync_time'] = sync_time
                    save_list.append(save_dict)
            if save_list:
                if self.__page != 1 and TmallSellerOrderEs().is_goods_in_db(last_goods_code, last_order_id) and int(
                    self.__catch_all) == 0:
                    TmallSellerOrderEs().update(save_list, async=True)
                    assert False, '已出现重复抓取, 停止爬虫.'
                TmallSellerOrderEs().update(save_list, async=True)
        except Exception as e:
            if isinstance(e, AssertionError):
                print('error', e.args[0])
                raise e
            else:
                print('--------error traceback--------')
                print(traceback.format_exc())
                print('解析第: {} 页报错: {}'.format(self.__page, e))

    def to_next_page(self):
        """
        点击下一页
        :return:
        """
        try:
            if self.__page == 10:
                # 点击展开显示更多页码
                self.__driver.find_element_by_class_name('pagination-mod__show-more-page-button___txdoB').click()
            else:
                self.__driver.find_element_by_class_name('pagination-next').click()
            if self.__start_page and self.__page < self.__start_page:
                self.__driver.find_element_by_class_name('pagination-mod__show-more-page-button___txdoB').click()
                time.sleep(1)
                btn = self.__driver.find_element_by_xpath(
                    '//*[@id="sold_container"]/div/div[5]/div[17]/div[2]/ul/div/div/input')
                btn.clear()
                btn.send_keys(self.__start_page)
                time.sleep(1)
                self.__driver.find_element_by_class_name('pagination-options-go').click()
                self.__page = self.__start_page + 1
            else:
                self.__page += 1
            time.sleep(1)
            self.catch_each_page()
        except Exception as e:
            if isinstance(e, AssertionError):
                print('点击下一页 error', e.args[0])
                raise e
            else:
                print('点击第: {} 页 error: {}'.format(self.__page, e))
        time.sleep(1)

    @classmethod
    def check_spider_active(cls):
        """
        检查爬虫是否在正常运行;
        通过检测爬虫数据的最后更新时间来判断爬虫是否在正常运行;
        :return:
        """
        last_modify_time = TmallSellerOrderEs().get_last_update_time()
        last_modify_time = Date(last_modify_time.get('sync_time'))
        compare_date = Date.now().plus_days(-2)
        print('last_modify_time', last_modify_time)
        print('compare_date', compare_date)
        if compare_date > last_modify_time:
            # 发送报警
            title = '生意参谋商家中心的订单商品快照数据抓取异常'
            text = '生意参谋商家中心的订单商品快照数据抓取异常, 数据超过两天未更新，最后更新时间: {}'.format(last_modify_time.format())
            DingTalk(ROBOT_TOKEN, title, text).enqueue()

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

    def _crack_slide_bar(self):
        """
        破解滑动验证码
        :return:
        """
        pass

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
            self.__driver.find_element_by_class_name('service-button-container')
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
