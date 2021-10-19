from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.model.es.SycmAiWords import SycmAiWords
from backstage_data_migrate.page.sycm.sycm_ai_tag_words import SycmAiTagWords
from cookie.config import ROBOT_TOKEN
from cookie.platform.taobao.login_base import *
from pyspider.helper.date import Date


class SycmSearchWords:
    """
    生意参谋 的搜索词抓取
    """
    URL = 'https://login.taobao.com/member/login.jhtml?from=sycm&full_redirect=true&style=minisimple&minititle=&minipara=0,0,0&sub=true&redirect_url=http://sycm.taobao.com/bda/items/effect/item_effect.htm?spm=a21ag.7634348.LeftMenu.d248.79ac71736jYMHM'
    # PROXY = '10.0.5.58:3128'
    PROXY = ''

    def __init__(self, username, password, start_days=1, end_days=1):
        self.__url = self.URL
        self.__username = username
        self.__password = password
        self.__start_days = start_days
        self.__end_days = end_days
        self.__driver = Webdriver().set_proxy(
            config.get('fixed_proxy', 'taobao') if not self.PROXY else self.PROXY).get_driver()
        self.__last_url = 'https://sycm.taobao.com/cc/macroscopic_monitor#item-rank'
        self.__page_count = 4

    def start_login(self):
        """
        登录sycm的入口
        :return:
        """
        self.login_entry()

    def login_entry(self):
        """"
        登录到 sycm
        """
        self.__driver.get(self.__url)
        time.sleep(5)
        # 登录
        self.login_operation()

        self.__driver.get(self.__last_url)
        time.sleep(3)
        # 登录成功，循环抓取热搜榜标签
        self.catch_words()
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
        time.sleep(2)
        # 判断是否有滑动验证码
        self._check_slide_bar()
        time.sleep(2)
        # 点击登录
        self.__driver.find_element_by_id("J_SubmitStatic").click()
        time.sleep(3)
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

    def catch_words(self):
        """
        抓取热搜词
        :return:
        """
        date_list = [Date.now().plus_days(-day).format(full=False) for day in
                     range(self.__end_days, self.__start_days + 1)]
        category_list = [
            {'50000697': '毛针织衫'},
            {'162116': '蕾丝衫/雪纺衫'},
            {'1622': '裤子'},
            {'1623': '半身裙'},
            {'50010850': '连衣裙'},
            {'162205': '牛仔裤'},
            {'50000671': 'T恤'},
            {'50013194': '毛呢外套'},
            {'162103': '毛衣'},
            {'50011277': '短外套'},
            {'50008899': '羽绒服'},
            {'50008898': '卫衣/绒衫'},
            {'50008897': '西装'},
            {'162104': '衬衫'},
            {'50008901': '风衣'},
            {'50008900': '棉衣/棉服'},
        ]
        key_type_list = [
            {'searchWord': '搜索词'},
            {'coreWord': '核心词'},
            {'attrWord': '修饰词'},
        ]
        aim_url = 'https://sycm.taobao.com/mc/mq/search_rank?activeKey={0}&cateFlag=2&cateId={1}&' \
                  'dateRange={2}%7C{2}&dateType=day&device=0&parentCateId=16'
        for date_value in date_list:
            for c in category_list:
                for k in key_type_list:
                    self.__page_count = 4
                    c_key, c_value = list(c.items())[0]
                    k_key, k_value = list(k.items())[0]
                    url = aim_url.format(k_key, c_key, date_value)
                    self.get_page_details(url, date_value, c_value, k_value)
        count = SycmAiWords().get_today_data_sum(Date.now().plus_days(-1).format(full=False))
        if count < 10000:
            # 报警
            title = '生意参谋搜索词数量过少报警'
            text = '生意参谋搜索词数量: {}'.format(count)
            DingTalk(ROBOT_TOKEN, title, text).enqueue()

    def get_page_details(self, url, date_str, category, key_type):
        """
        加载每个标签的详情页
        :param url: 详情页的 URL
        :param date_str: 日期时间，eg.2019-03-19
        :param category: 热搜词的中文类别: eg.毛呢外套
        :param key_type: 关键词类别: eg.核心词, 修饰词, 搜索词
        :return:
        """
        # 访问目标详情页
        self.__driver.get(url)
        time.sleep(2)
        self.has_cover_img()
        time.sleep(1)
        self.change_to_big_page()
        self.has_next_page(date_str, category, key_type)
        # html = self.__driver.page_source
        # print('type of html: {}'.format(type(html)))
        # SycmAiTagWords(html, date_str, category, key_type).enqueue()
        #
        # # 下一页
        # if self.hash_next_page() and retry < 5:
        #     return self.get_page_details(url, date_str, category, key_type, retry + 1)

    def change_to_big_page(self):
        """
        点击到100页的页码
        :return:
        """
        try:
            self.__driver.find_element_by_xpath('//*[@id="itemRank"]/div[2]/div/div[3]/div[1]/div/div/div/div').click()
            time.sleep(2)
            # 点击100页
            self.__driver.find_element_by_xpath('/html/body/div[8]/div/div/div/ul/li[4]').click()
            print('成功切换到100页')
            time.sleep(2)
        except Exception as e:
            print('没有成功切换到100页: {}'.format(e))
            self.__page_count = 20

    def has_cover_img(self):
        """
        点击去掉起始页的封面大图
        :return:
        """
        try:
            self.__driver.find_element_by_xpath('//*[@id="app"]/div/div[1]/div[3]/div[2]/div/span').click()
            print('有cover img')
            time.sleep(1)
        except Exception as e:
            print('没有cover img: {}'.format(e))

    def has_next_page(self, date_str, category, key_type):
        """
        判断是否有下一页
        :return:
        """
        for i in range(self.__page_count + 1):
            try:
                html = self.__driver.page_source
                print('type of html: {}, page: {}'.format(type(html), i + 1))
                SycmAiTagWords(html, date_str, category, key_type).enqueue()
                if i < self.__page_count:
                    self.__driver.find_element_by_class_name('ant-pagination-next').click()
            except Exception as e:
                print('点击第: {} 页失败: {}'.format(i, e))
            time.sleep(1)

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

    def _successfully_logged(self):
        """
        根据某个标签判断页面是否已经正确登录
        :return:
        """
        try:
            self.__driver.find_element_by_class_name('nameWrapper')
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
