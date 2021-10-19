from backstage_data_migrate.page.redbook.fashion_blogger_list import FashionBloggerList
from backstage_data_migrate.page.redbook_download_data_goods import RedbookGoodsDown
from backstage_data_migrate.page.redbook_download_data_shop import RedbookShopDown
from backstage_data_migrate.page.sycm.sycm_all_goods_flow import SycmAllGoodsFlow
from backstage_data_migrate.page.sycm.sycm_goods_download import SycmGoods
from pyspider.libs.base_handler import *
from pyspider.helper.date import Date
from backstage_data_migrate.page.sycm.sycm_yesterday_tmall_taobao_data import SycmYesterdayTmallTaobaoData
from pyspider.helper.logging import processor_logger
from backstage_data_migrate.page.sycm.sycm_tmall_databoard_msg import SycmTmallDataBoardMsg
from backstage_data_migrate.page.sycm.sycm_tmall_visitor_msg import SycmTmallVisitorMsg
from backstage_data_migrate.page.sycm.sycm_tmall_taobao_flow import SycmTmallTaobaoFlow
from backstage_data_migrate.page.redbook_databoard_msg import RedBookDataBoardMsg
from backstage_data_migrate.page.redbook_visitor_msg import RedbookVisitorMsg
from backstage_data_migrate.page.redbook_flow_data import RedbookFlowData
from backstage_data_migrate.page.jingdong_product_detail import JDProdictDetail
from backstage_data_migrate.page.jingdong_trade import JDTrade
from backstage_data_migrate.page.jingdong_view_flow import JDViewFlow
from backstage_data_migrate.page.jingdong_flow_data import JDFlowData

from cookie.model.data import Data


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    @every(minutes=50)
    def sycm_all_goods_flow(self):
        """
        生意参谋天猫后台 全量商品排行 的数据抓取
        这个是下载表格的
        :return:
        """
        day = 5
        devices = ['all_device', 'wifi']
        hour = int(Date.now().strftime('%H'))
        if hour == 8:
            processor_logger.info('到: {} 点了，开始抓取生意参谋天猫后台全量商品排行的数据'.format(hour))
            for username, pwd, channel in Data.CONST_USER_SYCM_BACKSTAGE:
                for _d in devices:
                    # day
                    for i in range(1, day + 1):
                        start_day = Date.now().plus_days(-i).format(full=False)
                        end_day = Date.now().plus_days(-i).format(full=False)
                        self.crawl_handler_page(SycmAllGoodsFlow(channel, _d, 'day', start_day, end_day, username))
                    # week
                    start_week = Date.now().plus_weeks(-1).to_week_start().format(full=False)
                    end_week = Date.now().plus_weeks(-1).to_week_end().format(full=False)
                    self.crawl_handler_page(SycmAllGoodsFlow(channel, _d, 'week', start_week, end_week, username))
                    # month
                    start_month = Date.now().plus_months(-1).to_month_start().format(full=False)
                    end_month = Date.now().plus_months(-1).to_month_end().format(full=False)
                    self.crawl_handler_page(SycmAllGoodsFlow(channel, _d, 'month', start_month, end_month, username))
        else:
            processor_logger.info('还没到点，暂不抓取')

    @every(minutes=50)
    def sycm_yesterday_data(self):
        """
        生意参谋昨天的天猫淘宝后台数据获取-流量看板
        这个获取的是json数据
        :return:
        """
        day = 6
        hour = int(Date.now().strftime('%H'))
        if 8 <= hour <= 11:
            processor_logger.info('到点了，开始抓取')
            usernames = Data.CONST_USER_SYCM_BACKSTAGE
            for _user, _pwd, _channel in usernames:
                for _day in range(1, day):
                    start_time = Date.now().plus_days(-_day).format(full=False)
                    end_time = start_time
                    self.crawl_handler_page(
                        SycmYesterdayTmallTaobaoData('day', start_time, end_time, '流量看板', _user, _channel))

                # 上周的数据
                week_start_day = Date.now().plus_weeks(-1).to_week_start().format(full=False)
                week_end_day = Date.now().plus_weeks(-1).to_week_end().format(full=False)
                self.crawl_handler_page(
                    SycmYesterdayTmallTaobaoData('week', week_start_day, week_end_day, '流量看板-week', _user, _channel))

                # 上个月的数据
                month_start_day = Date.now().plus_months(-1).to_month_start().format(full=False)
                month_end_day = Date.now().plus_months(-1).to_month_end().format(full=False)
                self.crawl_handler_page(
                    SycmYesterdayTmallTaobaoData('month', month_start_day, month_end_day, '流量看板-month', _user,
                                                 _channel))
        else:
            processor_logger.info('还没到点，暂不抓取')

    # @every(minutes=60)
    def sycm_today_data(self):
        """
        抓取生意参谋今天的数据，包括流量看板数据和访客数据
        访客数没有抓历史数据
        :return:
        """
        usernames = Data.CONST_USER_SYCM_BACKSTAGE
        for _user, _pwd, _channel in usernames:
            self.crawl_handler_page(SycmTmallDataBoardMsg(_user, _channel))
            self.crawl_handler_page(SycmTmallVisitorMsg(_user, _channel))

    @every(minutes=50)
    def sycm_flow_data(self):
        """
        生意参谋的天猫淘宝 流量来源 的数据获取
        oss本地不能测
        :return:
        """
        day = 6
        hour = int(Date.now().strftime('%H'))
        if hour == 8:
            processor_logger.info('到点了，开始抓取')
            # ----------------------------按 日 获取数据-----------------------------
            usernames = Data.CONST_USER_SYCM_BACKSTAGE
            for _user, _pwd, _channel in usernames:
                for _day in range(day):
                    yesterday = Date.now().plus_days(-_day - 1).format(full=False)
                    # pc
                    self.crawl_handler_page(SycmTmallTaobaoFlow(1, 'day', yesterday, yesterday, _user, _channel))
                    # wifi
                    self.crawl_handler_page(SycmTmallTaobaoFlow(2, 'day', yesterday, yesterday, _user, _channel))

                # ----------------------------按 周 获取数据-----------------------------
                week_start = Date.now().plus_weeks(-1).to_week_start().format(full=False)
                week_end = Date.now().plus_weeks(-1).to_week_end().format(full=False)
                # pc
                self.crawl_handler_page(SycmTmallTaobaoFlow(1, 'week', week_start, week_end, _user, _channel))
                # wifi
                self.crawl_handler_page(SycmTmallTaobaoFlow(2, 'week', week_start, week_end, _user, _channel))

                # ----------------------------按 月 获取数据-----------------------------
                month_start = Date.now().plus_months(-1).to_month_start().format(full=False)
                month_end = Date.now().plus_months(-1).to_month_end().format(full=False)
                # pc
                self.crawl_handler_page(SycmTmallTaobaoFlow(1, 'month', month_start, month_end, _user, _channel))
                # wifi
                self.crawl_handler_page(SycmTmallTaobaoFlow(2, 'month', month_start, month_end, _user, _channel))
            processor_logger.info("完成获取 生意参谋 天猫淘宝流量来源的数据!")
        else:
            processor_logger.info('还没到点，暂不抓取')

    # @every(minutes=50)
    # 取消这个位置的表格下载任务
    def sycm_goods_download(self):
        """
        生意参谋淘宝天猫渠道的 商品效果文件 下载
        :return:
        """
        hour = int(Date.now().strftime('%H'))
        days = 3
        # 每天八点开始下载表格
        if hour == 8:
            processor_logger.info('到: {} 点了，开始抓取'.format(hour))
            usernames = Data.CONST_USER_SYCM_BACKSTAGE
            for _user, _pwd, _channel in usernames:
                for day in range(1, days + 1):
                    self.crawl_handler_page(SycmGoods(_user, _channel, day))
        else:
            processor_logger.info('还没到点，暂不抓取')

    @every(minutes=50)
    def redbook_download_data(self):
        """
        小红书商家的商品流量表格下载
        :return:
        """
        hour = int(Date.now().strftime('%H'))
        days = 5
        username = Data.CONST_USER_REDBOOK_BACKSTAGE[0][0]
        # 每天8点开始下载表格
        if hour == 8:
            # 抓取近五天的数据
            for day in range(1, days + 1):
                self.crawl_handler_page(RedbookShopDown(username, day))
                self.crawl_handler_page(RedbookGoodsDown(username, day))
        else:
            processor_logger.info('还没到点，暂不抓取')

    @every(minutes=60)
    def redbook_data(self):
        """
        获取小红书的数据，包括流量看板数据和访客数据
        :return:
        """
        day = 6
        username, pwd = Data.CONST_USER_REDBOOK_BACKSTAGE[0]
        for _day in range(0, day):
            date = Date.now().plus_days(-_day).format(full=False)
            self.crawl_handler_page(RedBookDataBoardMsg(date, username))
            self.crawl_handler_page(RedbookVisitorMsg(date, username))

    @every(minutes=60 * 4)
    def redbook_flow_data(self):
        """
        获取小红书流量来源数据
        默认获取最近一天的数据，如果获取前天的数据，传参day=2
        :return:
        """
        day = 6
        username, pwd = Data.CONST_USER_REDBOOK_BACKSTAGE[0]
        for _day in range(1, day):
            self.crawl_handler_page(RedbookFlowData(username, day=_day))

    @every(minutes=50)
    def jingdong_data(self):
        """
        获取京东数据
        :return:
        """
        day = 6
        username = Data.CONST_USER_JD_BACKSTAGE
        hour = int(Date.now().strftime('%H'))
        if hour == 1 or (8 <= hour <= 10):
            processor_logger.info('到点了，开始抓取.')
            # ------------------------------按 日 获取数据----------------------
            for _day in range(1, day):
                yesterday = Date.now().plus_days(-_day).format(full=False)
                self.crawl_handler_page(JDProdictDetail(yesterday, yesterday, yesterday, '商品概况-day', username))
                self.crawl_handler_page(JDTrade(yesterday, yesterday, yesterday, '交易概况-day', username))
                self.crawl_handler_page(JDViewFlow(yesterday, yesterday, yesterday, '流量概况-day', username))

            this_year = Date.now().plus_weeks(-1).format(full=False).split('-', 1)[0]
            week_date = '99{0}{1}'.format(this_year,
                                          Date.now().now().plus_weeks(-1).year_week().split('第')[1].split('周')[0])
            week_start = Date.now().plus_weeks(-1).to_week_start().format(full=False)
            week_end = Date.now().plus_weeks(-1).to_week_end().format(full=False)
            this_month = Date.now().format(full=False).split('-')[1]
            month_date = this_year + this_month
            month_start = Date.now().to_month_start().format(full=False)
            month_end = Date.now().plus_days(-1).format(full=False)

            # 商品概况
            self.crawl_handler_page(JDProdictDetail(week_date, week_end, week_start, '商品概况-week', username))
            self.crawl_handler_page(JDProdictDetail(month_date, month_end, month_start, '商品概况-month', username))
            # 交易概况
            self.crawl_handler_page(JDTrade(week_date, week_end, week_start, '交易概况-week', username))
            self.crawl_handler_page(JDTrade(month_date, month_end, month_start, '交易概况-month', username))
            # 流量概况
            self.crawl_handler_page(JDViewFlow(week_date, week_end, week_start, '流量概况-week', username))
            self.crawl_handler_page(JDViewFlow(month_date, month_end, month_start, '流量概况-month', username))
        else:
            processor_logger.info('还没到点，暂不抓取')

    @every(minutes=50)
    def jingdong_flow_data(self):
        """
        获取京东流量来源数据
        :return:
        """
        day = 6
        hour = int(Date.now().strftime('%H'))
        if hour == 1 or (8 <= hour <= 10):
            processor_logger.info('到点了，开始抓取.')
        else:
            processor_logger.info('还没到点，暂不抓取')
            return
        username = Data.CONST_USER_JD_BACKSTAGE
        # 日期汇总
        this_year = Date.now().format(full=False).split('-', 1)[0]
        week_start = Date.now().to_week_start().format(full=False)
        week_end = Date.now().plus_days(-1).format(full=False)
        week_date = '99{0}{1}'.format(this_year, Date.now().year_week().split('第')[1].split('周')[0])
        month_start = Date.now().to_month_start().format(full=False)
        month_end = Date.now().plus_days(-1).format(full=False)
        month_date = month_start.replace('-', '')[:-2]

        # ------------------按 日 获取数据-----------------
        processor_logger.info("获取京东流量来源的数据")
        for i in range(day):
            today = Date.now().plus_days(-i - 1).format(full=False)

            day_start_date = today
            day_end_date = today
            day_date = today
            self.crawl_handler_page(JDFlowData('day', 'app', day_start_date, day_end_date, day_date, username))
            self.crawl_handler_page(JDFlowData('day', 'pc', day_start_date, day_end_date, day_date, username))
            self.crawl_handler_page(JDFlowData('day', 'wechat', day_start_date, day_end_date, day_date, username))
            self.crawl_handler_page(JDFlowData('day', 'mobileq', day_start_date, day_end_date, day_date, username))
            self.crawl_handler_page(JDFlowData('day', 'mport', day_start_date, day_end_date, day_date, username))

        # ------------------按 周 获取数据-----------------
        week_start_date = week_start
        week_end_date = week_end
        week_date = week_date
        self.crawl_handler_page(JDFlowData('week', 'app', week_start_date, week_end_date, week_date, username))
        self.crawl_handler_page(JDFlowData('week', 'pc', week_start_date, week_end_date, week_date, username))
        self.crawl_handler_page(JDFlowData('week', 'wechat', week_start_date, week_end_date, week_date, username))
        self.crawl_handler_page(JDFlowData('week', 'mobileq', week_start_date, week_end_date, week_date, username))
        self.crawl_handler_page(JDFlowData('week', 'mport', week_start_date, week_end_date, week_date, username))

        # ------------------按 月 获取数据-----------------
        month_start_date = month_start
        month_end_date = month_end
        month_date = month_date
        self.crawl_handler_page(JDFlowData('month', 'app', month_start_date, month_end_date, month_date, username))
        self.crawl_handler_page(JDFlowData('month', 'pc', month_start_date, month_end_date, month_date, username))
        self.crawl_handler_page(JDFlowData('month', 'wechat', month_start_date, month_end_date, month_date, username))
        self.crawl_handler_page(JDFlowData('month', 'mobileq', month_start_date, month_end_date, month_date, username))
        self.crawl_handler_page(JDFlowData('month', 'mport', month_start_date, month_end_date, month_date, username))
        processor_logger.info('完成获取京东流量来源的数据！')

    def redbook_blogger_live_data(self):
        """
        小红书获取时尚博主直播数据，带货数据，粉丝分析等数据
        :return:
        """
        user_name = Data.CONST_USER_REDBOOK_BLOGGER_LIVE[0][0]
        self.crawl_handler_page(FashionBloggerList(user_name, crawl_next_page=True))
