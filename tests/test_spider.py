import time

import requests
import unittest2 as unittest

from pyspider.libs.webdriver import Webdriver


class TestBackstageData(unittest.TestCase):

    def test_demo(self):
        print('start test....')
        self.assertEqual(1 + 2, 3)
        self.assertEqual(1 + 5, 6)

    def test_xiaohongshu(self):
        """
        小红书爬虫
        :rtype: object
        """
        # 时尚博主列表
        url = 'https://influencer.xiaohongshu.com/api/solar/cooperator/live/query?' \
              'column=livecomprehensiverank&sort=asc&location=&type=时尚&pageNum=3&pageSize=20&cps=true'
        # 粉丝分析-粉丝画像
        fans_profile_url = 'https://influencer.xiaohongshu.com/api/solar/kol/data/5ad8811a4eacab1fe241579f/fans_profile'
        # 粉丝分析-总粉丝趋势
        fans_overview_history_url = 'https://influencer.xiaohongshu.com/api/solar/kol/data/5ad8811a4eacab1fe241579f/fans_overall_history'
        # 直播数据-直播数据概况
        live_overall_url = 'https://influencer.xiaohongshu.com/api/solar/kol/data/5ad8811a4eacab1fe241579f/live_overall'
        # 直播数据-直播历史数据
        live_history_url = 'https://influencer.xiaohongshu.com/api/solar/kol/data/5ad8811a4eacab1fe241579f/live_history'
        # 带货数据
        cps_overall_url = 'https://influencer.xiaohongshu.com/api/solar/kol/data/5ad8811a4eacab1fe241579f/cps_overall'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
            'cookie': 'smidV2=20200708094241e5d75d4f7ac869090c9966f800fb0e78005bde8d995b94200; solar.beaker.session.id=1594172577572048885383; solar.sid=1594172577572048885383'
        }
        result = requests.get(url, headers=headers).text
        fans_result = requests.get(fans_profile_url, headers=headers).text
        print('result', result)
        print('fans_result', fans_result)

    def test_xiaohongshu_login(self):
        """
        小红书登录
        :return:
        """
        login_url = 'https://influencer.xiaohongshu.com/'
        driver = Webdriver().get_driver()
        driver.get(login_url)
        driver.find_element_by_class_name("login-big-button").click()
        time.sleep(20)
        driver.quit()
