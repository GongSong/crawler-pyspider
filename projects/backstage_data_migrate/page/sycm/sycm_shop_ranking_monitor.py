import time

from bs4 import BeautifulSoup

from backstage_data_migrate.model.es.sycm_shop_ranking_monitor import SycmShopRanMonitorEs
from pyspider.helper.date import Date
from pyspider.libs.webdriver import Webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class SycmShopRanMonitor:
    """
    概况：本爬虫获取排名前100的服装品牌店;
    数据获取的源地址：https://sycm.taobao.com/mc/mq/market_monitor?dateRange=2020-02-11%7C2020-03-11&dateType=recent30&device=0&sellerType=1&spm=a21ag.8718589.TopMenu.d1471.33db50a5Qpp8mW ;
    数据在生意参谋的[首页]-[市场]-[监控看版];
    获取内容：排名前100的服装品牌店的排行数据
    """
    URL = 'https://sycm.taobao.com/mc/mq/market_monitor?dateRange={yesterday}%7C{yesterday}&dateType=day&device=0&sellerType=1'
    DELAY = 10  # 等页面出现的最长等待时间
    PAGE_DELAY = 4  # 操作等待间隔

    def __init__(self, cookies):
        self.__cookies = cookies
        self.__driver = Webdriver().get_driver()

    def entry(self):
        try:
            # init
            print('init page')
            self.__driver.get(self.URL.format(yesterday=Date.now().plus_days(-1).format(full=False)))

            # set cookies
            print('set cookies')
            cookies = [cookie.strip() for cookie in self.__cookies.split(';')]
            for _c in cookies:
                k, v = _c.split('=', 1)
                self.__driver.add_cookie({'name': k, 'value': v})

            # fetch aim url
            self.__driver.get(self.URL.format(yesterday=Date.now().plus_days(-1).format(full=False)))
            time.sleep(self.PAGE_DELAY)

            # 移除弹窗
            self.remove_window()
            self.__driver.refresh()

            # wait for page load
            print('wait for page load')
            WebDriverWait(self.__driver, self.DELAY).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="monitor-card"]/div[2]/span[2]/h4[@class="card-content-title"]')))

            # 组装各级别数据的URL
            url_list = []

            yesterday = Date.now().plus_days(-1).format(full=False)
            one_week_ago = Date.now().plus_days(-7).format(full=False)
            one_month_ago = Date.now().plus_days(-30).format(full=False)
            # 7天
            recent7_url = 'https://sycm.taobao.com/mc/mq/market_monitor?dateRange={one_week_ago}|{yesterday}&dateType=recent7&device=0&sellerType=1'.format(
                one_week_ago=one_week_ago, yesterday=yesterday)
            # 30天
            recent30_url = 'https://sycm.taobao.com/mc/mq/market_monitor?dateRange={one_month_ago}|{yesterday}&dateType=recent30&device=0&sellerType=1'.format(
                one_month_ago=one_month_ago, yesterday=yesterday)
            # 日
            day_url = 'https://sycm.taobao.com/mc/mq/market_monitor?dateRange={yesterday}|{yesterday}&dateType=day&device=0&sellerType=1'.format(
                yesterday=yesterday)
            url_list.append(('recent7', yesterday, recent7_url))
            url_list.append(('recent30', yesterday, recent30_url))
            url_list.append(('day', yesterday, day_url))

            last_week_start = Date.now().plus_weeks(-1).to_week_start().format(full=False)
            last_week_end = Date.now().plus_weeks(-1).to_week_end().format(full=False)
            last_month_start = Date.now().plus_months(-1).to_month_start().format(full=False)
            last_month_end = Date.now().plus_months(-1).to_month_end().format(full=False)

            # 周
            week_url = 'https://sycm.taobao.com/mc/mq/market_monitor?dateRange={last_week_start}|{last_week_end}&dateType=week&device=0&sellerType=1'.format(
                last_week_start=last_week_start, last_week_end=last_week_end)
            # 月
            month_url = 'https://sycm.taobao.com/mc/mq/market_monitor?dateRange={last_month_start}|{last_month_end}&dateType=month&device=0&sellerType=1'.format(
                last_month_start=last_month_start, last_month_end=last_month_end)

            url_list.append(('week', last_week_start, week_url))
            url_list.append(('month', last_month_start, month_url))

            for date_type, type_begin_date, _url in url_list:
                try:
                    self.get_range_date_ranking(date_type, type_begin_date, _url)
                except Exception as e:
                    print('获取数据:{},{},{},失败:{}'.format(date_type, type_begin_date, _url, e))

        except Exception as e:
            print(e)
        finally:
            self.__driver.quit()

    def get_range_date_ranking(self, date_type, type_begin_date, url):
        """
        获取不同时间类型段内的排名数据
        :param date_type: 时间类型
        :param type_begin_date: 时间类型的开始时间
        :param url:
        :return:
        """
        print('时间类型:{}'.format(date_type))
        print('时间类型的开始时间:{}'.format(type_begin_date))
        print('获取数据:{}'.format(url))
        self.__driver.get(url)
        time.sleep(self.PAGE_DELAY)

        # 移除弹窗
        self.remove_window()

        # 展开页码
        self.expand_pagination()

        # 解析店铺内容
        soup = BeautifulSoup(self.__driver.page_source, 'lxml')
        shops = soup.find_all('tbody', 'ant-table-tbody')
        if len(shops) > 1:
            data_list = []
            sync_time = Date.now().format_es_utc_with_tz()
            shop_items = shops[1].find_all('tr')
            shop_items[0].find_all('td')[0].find('div', 'sycm-common-shop-td')['title']
            for item in shop_items:
                shop_name = item.find_all('td')[0].find('div', 'sycm-common-shop-td')['title']
                try:
                    ranking = int(
                        item.find_all('td')[1].find('span', 'alife-dt-card-common-table-sortable-value').get_text())
                except Exception as e:
                    print('int ranking e: {}'.format(e))
                    ranking = 0
                save_data = {
                    'date_type': date_type,
                    'type_begin_date': type_begin_date,
                    'shop_name': shop_name,
                    'ranking': ranking,
                    'sync_time': sync_time,
                }
                data_list.append(save_data)
            SycmShopRanMonitorEs().update(data_list, async=True)
        else:
            print('没有获取到店铺数据')

    def expand_pagination(self, retry=4):
        """
        给监控店铺部分的数据全部展开
        :return:
        """
        try:
            time.sleep(self.PAGE_DELAY)
            self.__driver.find_element_by_xpath(
                '//*[@id="mqMyMonitorshop"]/div[2]/div/div[3]/div[1]/div/div/div/div/div').click()
            time.sleep(self.PAGE_DELAY)
            # self.__driver.find_element_by_xpath('/html/body/div[8]/div/div/div/ul/li[5]').click()
            self.__driver.find_element_by_xpath('//ul[@role="listbox"][1]/li[5]').click()
            print('监控店铺部分的数据全部展开成功')
            time.sleep(self.PAGE_DELAY)
        except Exception as e:
            print('监控店铺部分的数据全部展开失败: {}, 剩余重试次数:{}'.format(e, retry - 1))
            if retry > 0:
                return self.expand_pagination(retry - 1)

    def remove_window(self):
        """
        移除弹窗
        :return:
        """
        try:
            if self.has_element('ant-modal-close-x'):
                self.__driver.find_element_by_class_name('ant-modal-close-x').click()
            elif self.has_element('ebase-ImageTips__dsImageTipsCloseBtn'):
                self.__driver.find_element_by_class_name('ebase-ImageTips__dsImageTipsCloseBtn').click()
            else:
                print('没找到弹窗')
        except Exception as e:
            print(e)
            print('没有弹窗')

    def has_element(self, class_name):
        """
        判断是否有 class 为 class_name 的元素
        :param class_name:
        :return:
        """
        try:
            self.__driver.find_element_by_class_name(class_name)
            return True
        except Exception as e:
            print(e)
            print('class :{}'.format(class_name))
            return False


if __name__ == '__main__':
    cookies = 'miniDialog=true; t=cfcedf61d00aedfa95d78dc444244be3; cookie2=1c8072fd8d9faf5885959ece809392e6; _tb_token_=7e31b3363ee5e; JSESSIONID=80C5B20D347CCDF686C8084D6FC3137B; _samesite_flag_=true; x=3165080793; sgcookie=E9SzqVJpP%2BYUoNZDZ25Qm; unb=4112990058; sn=icy%E6%97%97%E8%88%B0%E5%BA%97%3A%E7%A0%94%E5%8F%91; uc1=cookie14=UoTUPvAqVcz7Lg%3D%3D&lng=zh_CN; csg=2a51fa55; skt=7470226d8114a018; cna=NuDxFt1c7HsCAXxKajqOdFDv; _euacm_ac_l_uid_=4112990058; 4112990058_euacm_ac_c_uid_=3165080793; 4112990058_euacm_ac_rs_uid_=3165080793; _euacm_ac_rs_sid_=479195376; v=0; tfstk=c_XCBJT_LaBNxMxIT_ZwUCAc61JRZlnXVWThA1OSZgbYPEjCiNH2oMz1Z4H9Mh1..; l=dBMMzYmcQH4fHsU9BOfgIS7c3xQ9iIRfGsPr0J2X5ICPOc1vf3NOWZqNBQ8JCnGVn6kWR3SkMlheBv8SMy4OhC4NtnTHAx8ZFdLh.; isg=BHBwom-Y2hnUxoYd6IiyTZPYQTjCuVQDrPrv6mrBvkuEJRTPEs1FkqDXeS1FtQzb'
    SycmShopRanMonitor(cookies, 3).entry()
