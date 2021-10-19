import gevent.monkey

from cookie.config import CRAWL_TMALL_SHOPS
from cookie.platform.taobao.tmall_shop_cookies import TmallShopCookies
from cookie.platform.xhs.redbook_blogger_live import RedbookBloggerLive

gevent.monkey.patch_ssl()
import json
from cookie.page.tableau_cookie_check import TableauCoCheck
from cookie.platform.tableau.tableau_cookie import TableauCookie
from pyspider.helper.crawler_utils import CrawlerHelper
import random
import time
import fire
from backstage_data_migrate.page.taobao_account_synchron import TaobaoAccount
from cookie.platform.jingdong.jingdong_cookie import JingDongLogin
from cookie.platform.taobao.huoniu import Huoniu
from cookie.platform.taobao.manager_soft import ManagerSoft
from cookie.platform.taobao.sycm import Sycm
from cookie.platform.taobao.sycm_search_words import SycmSearchWords
from cookie.platform.taobao.taobao_backstage_comment import TaobaoBackComment
from cookie.platform.taobao.taobao_shop_goods import TaobaoShopGoods
from cookie.platform.taobao.tbk import Tbk
from cookie.platform.taobao.myseller import Myseller
from cookie.platform.taobao.taobao_comment import TaobaoComment
from cookie.platform.taobao.tmall_backstage_comment import TmallBackComment
from cookie.platform.taobao.tmall_comment import TmallComment
from cookie.platform.taobao.update_tmall_seller_cookies import TmallSeller
from cookie.platform.weipinhui.weipinhui import Weipinhui
from cookie.platform.xhs.redbook import Redbook
from crawl_taobao_goods_migrate.model.result import Result
from monitor_icy_comments_migrate.page.catch_tmall_comments import CatchTmallComments
from pyspider.helper.date import Date
from talent.page.rpt import Rpt as RptPage
from talent.page.tbk import Tbk as TbkPage
from talent.page.tbk_order_details import TbkOrderDetails
from cookie.model.data import Data as CookieData


class Cron:
    def update_huoniu_cookies(self):
        """
        更新火牛 cookies
        :return:
        """
        for account, password in CookieData.CONST_USER_TAOBAO_HUONIU:
            cookies = Huoniu(account, password).update_cookies()
            print('huoniu', account, cookies)
        exit()

    def update_tbk_cookies(self):
        """
        更新淘宝客 cookies, 以及入队上传数据到ai的任务
        :return:
        """
        print('开始更新淘宝客 cookies, 以及入队上传数据到ai的任务,time:{}'.format(Date.now().format()))
        for account, password in CookieData.CONST_USER_TAOBAO_TBK:
            cookies = Tbk(account, password).update_cookies()
            print('tbk', account, cookies)
            yesterday = Date.now().plus_days(-1).strftime("%Y-%m-%d")
            RptPage(Date.now().plus_days(-30).strftime("%Y-%m-%d"), yesterday, account, 'rpt').enqueue()
            TbkPage(Date.now().plus_days(-60).strftime("%Y-%m-%d"), yesterday, account, 'tbk').enqueue()
            TbkPage(Date.now().plus_days(-90).format(full=False),
                    Date.now().plus_days(-59).format(full=False),
                    account, 'tbk').enqueue()

            # 联盟商家中心，成交订单明细
            print('获取联盟商家中心的成交订单明细')
            order_days = 5  # 获取近5天的数据
            for day_num in range(1, order_days + 1):
                order_day_str = Date.now().plus_days(-day_num).format(full=False)
                TbkOrderDetails(order_day_str, order_day_str, account, 'tbkOrderDetails').enqueue()
            # 随机暂停
            time.sleep(random.randint(10, 20))
        exit()

    def update_sycm_cookies(self):
        """
        更新生意参谋的 cookies
        :return:
        """
        print('\n开始更新生意参谋的 cookies,time:{}'.format(Date.now().format()))
        for account, password, channel in CookieData.CONST_USER_SYCM_BACKSTAGE:
            cookies = Sycm(account, password).update_cookies()
            print('sycm', account, cookies)
            time.sleep(random.randint(10, 20))
        exit()

    def update_tmall_seller_cookies(self, start_page, end_page, catch_all=0):
        """
        天猫商家后台的cookie获取；
        目前有以下几个页面的数据：
        1, 商家中心: https://trade.taobao.com/trade/itemlist/list_sold_items.htm
        :param start_page: 跳转抓取的页码, 为0则代表从第一页开始抓取
        :param end_page: 抓取结束的页码
        :param catch_all: 是否抓取全量的数据，默认为0，不抓全量；1：抓取全量
        :return:
        """
        print('天猫商家后台的cookie获取,time:{}'.format(Date.now().format()))
        try:
            # 检测爬虫是否在正常运行
            TmallSeller.check_spider_active()
            # 抓取数据
            account, password, channel = CookieData.CONST_USER_SYCM_BACKSTAGE[0]
            TmallSeller(account, password, start_page, end_page, catch_all).start_login()
        except Exception as e:
            print('update_tmall_seller_cookies error', e)
        exit()

    def fetch_sycm_search(self, start_days=1, end_days=1):
        """
        生意参谋 搜索词热度数据 抓取入口;
        只抓取天猫的cookie
        :return:
        """
        print('生意参谋 搜索词热度数据 抓取入口,time:{}'.format(Date.now().format()))
        account, password, channel = CookieData.CONST_USER_SYCM_BACKSTAGE[0]
        SycmSearchWords(account, password, start_days, end_days).start_login()
        exit()

    def update_myseller_cookies(self):
        """
        更新卖家中心的 cookies，可以下到订单数据
        :return:
        """
        print('更新卖家中心的 cookies，可以下到订单数据,time:{}'.format(Date.now().format()))
        for account, password in CookieData.CONST_USER_TAOBAO_MYSELLER:
            cookies = Myseller(account, password).update_cookies()
            print('myseller', account, cookies)
            TaobaoAccount(account).enqueue()
        exit()

    def update_taobao_shop_goods(self):
        """
        抓取淘宝店铺下的所有商品
        :return:
        """
        print('抓取淘宝店铺下的所有商品,time:{}'.format(Date.now().format()))
        all_shop_id = Result().find_all_shop_id()
        id_list = list()
        for _id in all_shop_id:
            shop_id = _id.get('result').get('shop_id')
            id_list.append(str(shop_id))
        TaobaoShopGoods(id_list).catch_all_goods()
        exit()

    def update_taobao_comment_cookies(self):
        """
        更新淘宝评论 cookie 池
        :return:
        """
        while True:
            try:
                cookies = TaobaoComment(581239730924, 1595046216).update()
                print(cookies)
                time.sleep(5)
            except Exception as e:
                print(e)

    def update_manager_soft(self):
        """
        获取天猫商品的 类目、商家编码、商品编码等数据
        :return:
        """
        print('获取天猫商品的 类目、商家编码、商品编码等数据, 时间:{}'.format(Date.now().format()))
        for account, password, channel in CookieData.CONST_USER_TAOBAO_MANAGER_SOFT:
            cookies = ManagerSoft(account, password, channel).get_cookies_dict()
            print('finished upload manager soft')
            time.sleep(5)
        exit()

    def update_tmall_comment_cookies(self):
        """
        更新天猫评论 cookie 池
        :return:
        """
        while True:
            try:
                cookies = TmallComment(581258212753, 2089019212).update()
                print(cookies)
                time.sleep(5)
            except Exception as e:
                print(e)

    def update_tmall_back_comment_cookies(self):
        """
        更新 天猫后台账号评论 的 cookie 池
        :return:
        """
        for account, password in CookieData.CONST_USER_TMALL_BACK_COMMENT:
            cookies = TmallBackComment(account, password).update_cookies()
            print('tmall backstage comment', account, cookies)
            CatchTmallComments(account).enqueue()
        exit()

    def update_taobao_back_comment_cookies(self):
        """
        更新 淘宝后台评论账号评论 的 cookie 池
        :return:
        """
        for account, password in CookieData.CONST_USER_TAOBAO_BACK_COMMENT:
            cookies = TaobaoBackComment(account, password).update_cookies()
            print('taobao backstage comment', account, cookies)
            # CatchTaoBaoComments(account).enqueue()
        exit()

    def update_weipinhui_backstage_cookies(self):
        """
        更新 唯品会后台账号 的 cookie 池
        :return:
        """
        print('更新 唯品会后台账号 的 cookie 池,time:{}'.format(Date.now().format()))
        for account, password in CookieData.CONST_USER_WEIPINHUI:
            cookies = Weipinhui(account, password).update_cookies()
            print('weipinhui backstage cookie', account, cookies)
        exit()

    def update_redbook_backstage_cookies(self):
        """
        更新 小红书后台账号 的 cookie 池
        :return:
        """
        print('更新 小红书后台账号 的 cookie 池,time:{}'.format(Date.now().format()))
        for account, password in CookieData.CONST_USER_REDBOOK_BACKSTAGE:
            cookies = Redbook(account, password).update_cookies()
            print('redbook backstage cookie', account, cookies)
        exit()

    def update_redbook_blogger_live_cookies(self):
        print('更新 小红书博主直播数据的后台 的 cookie 池,time:{}'.format(Date.now().format()))
        for account, password in CookieData.CONST_USER_REDBOOK_BLOGGER_LIVE:
            cookies = RedbookBloggerLive(account, password).update_cookies()
            print('redbook backstage blogger live cookie', account, cookies)
            break
        exit()

    def update_jingdong_backstage_cookies(self):
        """
        更新 京东后台账号 的 cookie 池
        :return:
        """
        for account, password in CookieData.CONST_USER_JINGDONG:
            cookies = JingDongLogin(account, password).login()
            print('jingdong backstage cookie', account, cookies)
        exit()

    def maintain_tableau_cookies(self):
        """
        维持tableau的cookie长期有效
        :return:
        """
        print('维持tableau的cookie长期有效,time:{}'.format(Date.now().format()))
        username, password = CookieData.CONST_USER_TABLEAU[0]
        # 检测cookie是否失效
        tableau_obj = TableauCoCheck(username)
        status, result = CrawlerHelper().get_sync_result(tableau_obj)
        if status == 0 and 'result' in result and json.loads(result).get('result', {}).get('totalCount'):
            print('cookie 没有失效, 时间: {}'.format(Date.now().format()))
        else:
            print('cookie 失效了，重新登录, 时间: {}'.format(Date.now().format()))
            # 登录获取tableau的cookies
            cookies = TableauCookie(username, password).update_cookies()
            print('tableau cookies', username, cookies)
            exit()

    def update_tmall_shop_cookies(self, shop_url=""):
        """
        更新天猫店铺的cookies
        :param shop_url:
        :return:
        """
        if not shop_url:
            shop_url = random.choice(CRAWL_TMALL_SHOPS)
        TmallShopCookies(shop_url).catch_page()

    def clear_tmall_shop_cookies(self):
        """
        清空天猫店铺的老cookies, 删除过期的cookies
        :return:
        """
        print('开始清空天猫店铺的过期cookies, now:{}'.format(Date.now().format()))
        CookieData.sexpire_del(CookieData.CONST_PLATFORM_TMALL_SHOP_GOODS, 3600 * 24 * 2)
        print('清空天猫店铺的过期cookies完成')


if __name__ == '__main__':
    fire.Fire(Cron)
