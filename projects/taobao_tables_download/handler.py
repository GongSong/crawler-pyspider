from pyspider.libs.base_handler import *
from pyspider.helper.date import Date
from cookie.model.data import Data
from taobao_tables_download.config import *
from taobao_tables_download.model.es_query import GoodsEs
from taobao_tables_download.page.goods_flow_sources_entry import GoodsFlowEntry
from taobao_tables_download.page.shop_all_day import ShopAllDay
from taobao_tables_download.page.shop_all_week import ShopAllWeek
from taobao_tables_download.page.shop_all_month import ShopAllMonth
from taobao_tables_download.page.shop_hour_day import ShopHourDay
from taobao_tables_download.page.shop_flow_day import ShopFlowDay
from taobao_tables_download.page.shop_flow_week import ShopFlowWeek
from taobao_tables_download.page.shop_flow_month import ShopFlowMonth
from taobao_tables_download.page.shop_keyword_day import ShopKeywordDay
from taobao_tables_download.page.shop_category_day import ShopCategoryDay
from taobao_tables_download.page.shop_category_week import ShopCategoryWeek
from taobao_tables_download.page.shop_category_month import ShopCategoryMonth


class Handler(BaseHandler):
    """
    该项目下所有文件于凌晨2点开始抓取，如果没有获取到对应渠道的cookie，
    会延迟间隔一个小时重新抓取，直到抓取到为止或者直到重试至中午12时为止。
    """
    crawl_config = {
    }

    def on_start(self):
        self.goods_flow_entry()

    # @every(minutes=50)
    def goods_flow_entry(self):
        """
        每天八点开始抓取；
        抓取天猫每个商品的流量来源；
        停止运行（被新的爬虫所替代）；
        :return:
        """
        hour = int(Date.now().strftime('%H'))
        days = 3
        # 每天八点开始下载表格
        if hour == 8:
            processor_logger.info('到: {} 点了，开始抓取'.format(hour))
            date_list = ['day', 'week', 'month']
            for items in Data.CONST_USER_SYCM_BACKSTAGE:
                for d in date_list:
                    if d == 'day':
                        for i in range(1, days):
                            self.download_entry(items[0], items[2], d, i, i)
                    else:
                        self.download_entry(items[0], items[2], d)
        else:
            processor_logger.info('还没到点，暂不抓取')

    def download_entry(self, username, channel, date_type='day', start_date_num=1, end_date_num=1):
        if channel == CHANNLE_TAOBAO:
            query_words = 'taobaoGoodsId'
        elif channel == CHANNLE_TMALL:
            query_words = 'tmallGoodsIds'
        else:
            assert False, 'channel 错误'

        device_list = [('pc', 1), ('无线', 2)]
        inner_date_type = self.get_date_args(date_type, start_date_num, end_date_num)
        kdate_type = inner_date_type[0]
        kdate_words = inner_date_type[1]
        kdate_merge = inner_date_type[2]

        all_goods = GoodsEs().get_goods_by_channle(query_words)
        for goods in all_goods:
            for g in goods:
                # 被抓取的 goods_id
                catch_goods = g.get(query_words, '')
                for client, kv in device_list:
                    if channel == CHANNLE_TAOBAO:
                        self.crawl_handler_page(GoodsFlowEntry(client, channel, username, kdate_type, kdate_words,
                                                               kdate_merge, kv, catch_goods))
                    elif channel == CHANNLE_TMALL:
                        for cg in catch_goods:
                            self.crawl_handler_page(GoodsFlowEntry(client, channel, username, kdate_type, kdate_words,
                                                                   kdate_merge, kv, cg))

    def get_date_args(self, date_type, start_date_num=1, end_date_num=1):
        """
        根据不同的日期类型返回对应的构造参数信息
        :param date_type: 日期类型，比如：day, week, month
        :param start_date_num: Date 库的添加日期的数量，默认为 1; 比如：Date.now().plus_days(days=1)
        :param end_date_num: Date 库的添加日期的数量，默认为 1; 比如：Date.now().plus_days(days=1)
        :return: 参数信息，例子: ['day', '日', '2019-03-06|2019-03-06']
        """
        date_list = {
            'day': '日',
            'week': '周',
            'month': '月',
        }
        if date_type == 'day':
            start_date = Date.now().plus_days(-end_date_num).format(full=False)
            end_date = Date.now().plus_days(-start_date_num).format(full=False)
        elif date_type == 'week':
            start_date = Date.now().plus_weeks(-end_date_num).to_week_start().format(full=False)
            end_date = Date.now().plus_weeks(-start_date_num).to_week_end().format(full=False)
        elif date_type == 'month':
            start_date = Date.now().plus_months(-end_date_num).to_month_start().format(full=False)
            end_date = Date.now().plus_months(-start_date_num).to_month_end().format(full=False)
        else:
            assert False, 'date type 类型错误'
        date_merge = start_date + '|' + end_date
        return [date_type, date_list[date_type], date_merge]

    @every(minutes=50)
    def shop_all_day(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_整体_自然日_自动更新', today])
                start_date_day = Date.now().plus_days(-30).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopAllDay(file_name, start_date_day, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_all_week(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_整体_自然周_自动更新', today])
                start_date_week = Date.now().plus_days(-56).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopAllWeek(file_name, start_date_week, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_all_month(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_整体_自然月_自动更新', today])
                start_date_month = Date.now().to_month_start().plus_months(-6).format(full=False)
                end_date_month = Date.now().plus_months(-1).to_month_end().format(full=False)
                self.crawl_handler_page(ShopAllMonth(file_name, start_date_month, end_date_month, _usr, _channel))

    @every(minutes=50)
    def shop_hour_day(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_分小时_自然日_自动更新', today])
                start_date_day = Date.now().plus_days(-30).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopHourDay(file_name, start_date_day, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_flow_day(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_流量来源_自然日_自动更新', today])
                start_date_day = Date.now().plus_days(-30).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopFlowDay(file_name, start_date_day, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_flow_week(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_流量来源_自然周_自动更新', today])
                start_date_week = Date.now().plus_days(-56).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopFlowWeek(file_name, start_date_week, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_flow_month(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_流量来源_自然月_自动更新', today])
                start_date_month = Date.now().to_month_start().plus_months(-6).format(full=False)
                end_date_month = Date.now().plus_months(-1).to_month_end().format(full=False)
                self.crawl_handler_page(ShopFlowMonth(file_name, start_date_month, end_date_month, _usr, _channel))

    @every(minutes=50)
    def shop_keyword_day(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_引流关键词_自然日_自动更新', today])
                start_date_day = Date.now().plus_days(-30).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopKeywordDay(file_name, start_date_day, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_category_day(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_类目构成_自然日_自动更新', today])
                start_date_day = Date.now().plus_days(-30).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopCategoryDay(file_name, start_date_day, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_category_week(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_类目构成_自然周_自动更新', today])
                start_date_week = Date.now().plus_days(-56).format(full=False)
                end_date = Date.now().plus_days(-day).format(full=False)
                self.crawl_handler_page(ShopCategoryWeek(file_name, start_date_week, end_date, _usr, _channel))

    @every(minutes=50)
    def shop_category_month(self):
        if int(Date.now().strftime('%H')) == 2:
            for _usr, _pwd, _channel in Data.CONST_USER_SYCM_BACKSTAGE:
                day = 1
                today = Date.now().plus_days(1 - day).format(full=False)
                file_name = 'T'.join(['店铺_类目构成_自然月_自动更新', today])
                start_date_month = Date.now().to_month_start().plus_months(-6).format(full=False)
                end_date_month = Date.now().plus_months(-1).to_month_end().format(full=False)
                self.crawl_handler_page(ShopCategoryMonth(file_name, start_date_month, end_date_month, _usr, _channel))
