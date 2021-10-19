import fire
import traceback

from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.config import OUR_ROBOT_TOKEN
from backstage_data_migrate.model.backstage_migrate import Backstage
from backstage_data_migrate.model.es.tmall_seller_order import TmallSellerOrderEs
from backstage_data_migrate.model.mysql.goods_flow_sources import GoodsFlowSources
from backstage_data_migrate.page.file_download.sycm_goods_traffic_sources import SycmGoodsTraSources
from backstage_data_migrate.page.jingdong_goods_details import JDGoodsDetailsDl
from backstage_data_migrate.page.sycm.sycm_promotion_amount import SycmPromAmount
from backstage_data_migrate.page.sycm.sycm_shop_ranking_monitor import SycmShopRanMonitor
from cookie.model.data import Data as CookieData
from pyspider.helper.date import Date
from pyspider.helper.excel import Excel
from pyspider.helper.excel_reader import ExcelReader
from pyspider.helper.string import merge_str, number_convert
from pyspider.libs.oss import oss


class Cron:
    def monitor_databoard_hour(self):
        """
        监控生意参谋的 数据看板和访客数 的实时数据，按小时维度监控
        :return:
        """
        now_hour = Date.now().to_hour_start().timestamp()
        create_time = Date(now_hour).to_hour_start().format()
        usernames = CookieData.CONST_USER_SYCM_BACKSTAGE
        data_type_list = ['访客数', '流量看板']
        for _user, _pwd, _channel in usernames:
            website = 'sycm:{}'.format(_channel)
            for _type in data_type_list:
                builder = {
                    'result.website': website,
                    'result.data_type': _type,
                    'result.create_time': create_time,
                    'result.hour': now_hour,
                }
                count = Backstage().find(builder).count()
                if count < 1:
                    print('没有 {}{}:{} 的数据'.format(_channel, _type, create_time))
                    title = '生意参谋没有 {}{}:{} 的数据报警'.format(_channel, _type, create_time)
                    text = '生意参谋没有 {}{}:{} 的数据，请及时处理，检查cookie是否已失效'.format(_channel, _type, create_time)
                    DingTalk(OUR_ROBOT_TOKEN, title, text).enqueue()
                print('{}{}:{} 的数据数量: {}'.format(_channel, _type, create_time, count))

    def generate_tmall_seller_orders_table(self, start_day, end_day):
        """
        生成指定时间范围内的天猫卖家中心订单表格
        :param start_day: 开始时间, eg, 1
        :param end_day: 结束时间, eg, 30
        :return:
        """
        start_time = Date.now().plus_days(-end_day).to_day_start().format_es_utc_with_tz()
        end_time = Date.now().plus_days(-start_day).to_day_end().format_es_utc_with_tz()
        print('start_time', start_time)
        print('end_time', end_time)
        excel = Excel() \
            .add_header('order_id', '订单号') \
            .add_header('goods_code', '商品编码') \
            .add_header('delivery_time', '快照发货时间')
        goods_list = TmallSellerOrderEs().find_goods_by_order_create_time(start_time, end_time)
        for _goods in goods_list:
            for _g in _goods:
                excel.add_data(_g)
        with open('data.xlsx', 'wb') as file:
            file.write(excel.execute())

    def download_goods_traffic_sources(self, start_day, end_day):
        """
        获取生意参谋每个商品的 商品流量来源 数据
        :param start_day: 开始日期, eg: 1
        :param end_day: 结束日期, eg: 5
        :return:
        """
        username, pwd, channel = CookieData.CONST_USER_SYCM_BACKSTAGE[0]
        for day in range(start_day, end_day + 1):
            try:
                sycm_goods = SycmGoodsTraSources(day, day, username, channel)
                # 启动文件下载
                sycm_goods.start()
            except Exception as e:
                print('第: {} 天的抓取异常error: {}'.format(day, e))
        # 校验数据是否已经被抓取到，并以此为依据发送报警信息
        SycmGoodsTraSources.check()

    def save_goods_flow_sources_to_mysql(self, start_day, days):
        """
        把商品流量来源保存到mysql
        :param start_day: 开始的天数, eg: 1
        :param days: 写入近几天的流量来源数据, eg: 5
        :return:
        """
        print('开始把商品流量来源保存到mysql')
        # 无效的文件大小
        invalid_size = 13824
        # 初始化数据库
        if not GoodsFlowSources.table_exists():
            GoodsFlowSources.create_table()

        for day in range(start_day, days):
            day_date = Date.now().plus_days(-day).format(full=False)
            try:
                file_name = 'tmall/goods_traffic_sources/day/{day_date}/[生意参谋商品流量来源][无线端]'.format(day_date=day_date)
                file_path = oss.get_key(oss.CONST_SYCM_GOODS_TRAFFIC_SOURCES, file_name)
                print('file_path', file_path)
                update_time = Date.now().datetime
                paths = oss.keys(file_path)
                for _path in paths:
                    obj_list = _path.object_list
                    for _obj in obj_list:
                        # 需要在这里加入try catch，防止读取某个文件失败导致所有的读取都失败
                        key_name = _obj.key
                        file_size = _obj.size
                        if file_size <= invalid_size:
                            continue
                        file = oss.get_data(key_name)
                        file_format_data = ExcelReader(file_contents=file) \
                            .add_header('sources_name', '来源名称') \
                            .add_header('visitor_num', '访客数') \
                            .add_header('page_views', '浏览量') \
                            .add_header('pay_amount', '支付金额') \
                            .add_header('percent_visitor', '浏览量占比') \
                            .add_header('store_jump_num', '店内跳转人数') \
                            .add_header('store_jump_out_num', '跳出本店人数') \
                            .add_header('collect_num', '收藏人数') \
                            .add_header('add_pur_num', '加购人数') \
                            .add_header('buyer_num', '下单买家数') \
                            .add_header('order_conv_rate', '下单转化率') \
                            .add_header('payment_num', '支付件数') \
                            .add_header('buyer_pay_num', '支付买家数') \
                            .add_header('payment_conv_rate', '支付转化率') \
                            .add_header('direct_payment_buyer_num', '直接支付买家数') \
                            .add_header('collect_paid_buyer_num', '收藏商品-支付买家数') \
                            .add_header('fans_paid_buyer_num', '粉丝支付买家数') \
                            .add_header('add_pur_paid_buyer_num', '加购商品-支付买家数') \
                            .get_result()

                        # 添加额外数据
                        goods_id = key_name.split('[无线端][', 1)[1].split(']', 1)[0]
                        for _data in file_format_data:
                            _data['percent_visitor'] = number_convert(_data['percent_visitor'], 'float', ',')
                            _data['order_conv_rate'] = number_convert(_data['order_conv_rate'], 'float', ',')
                            _data['payment_conv_rate'] = number_convert(_data['payment_conv_rate'], 'float', ',')
                            _data['visitor_num'] = number_convert(_data['visitor_num'], 'int', ',')
                            _data['page_views'] = number_convert(_data['page_views'], 'int', ',')
                            _data['pay_amount'] = number_convert(_data['pay_amount'], 'float', ',')
                            _data['store_jump_num'] = number_convert(_data['store_jump_num'], 'int', ',')
                            _data['store_jump_out_num'] = number_convert(_data['store_jump_out_num'], 'int', ',')
                            _data['collect_num'] = number_convert(_data['collect_num'], 'int', ',')
                            _data['add_pur_num'] = number_convert(_data['add_pur_num'], 'int', ',')
                            _data['buyer_num'] = number_convert(_data['buyer_num'], 'int', ',')
                            _data['payment_num'] = number_convert(_data['payment_num'], 'int', ',')
                            _data['buyer_pay_num'] = number_convert(_data['buyer_pay_num'], 'int', ',')
                            _data['direct_payment_buyer_num'] = number_convert(_data['direct_payment_buyer_num'], 'int',
                                                                               ',')
                            _data['collect_paid_buyer_num'] = number_convert(_data['collect_paid_buyer_num'], 'int',
                                                                             ',')
                            _data['fans_paid_buyer_num'] = number_convert(_data['fans_paid_buyer_num'], 'int', ',')
                            _data['add_pur_paid_buyer_num'] = number_convert(_data['add_pur_paid_buyer_num'], 'int',
                                                                             ',')
                            _data['main_id'] = merge_str(goods_id, day_date, _data['sources_name'])
                            _data['goods_id'] = goods_id
                            _data['date_str'] = day_date
                            _data['update_time'] = update_time
                        GoodsFlowSources.replace_many(file_format_data).execute()
                        print('本次写入mysql完成, 日期:{}'.format(day_date))
            except Exception as e:
                print('保存日期:{}的商品流量来源失败:{}'.format(day_date, e))
                print(traceback.format_exc())

    def get_jingdong_goods_detail_file(self):
        """
        下载京东后台的商品明细表格，解压缩后保存
        :return:
        """
        print('开始下载京东后台的商品明细表格, time:{}'.format(Date.now().format()))
        JDGoodsDetailsDl().action()
        print('京东后台的商品明细表格下载完成, time:{}'.format(Date.now().format()))
        exit()

    def sycm_ranking_promotion(self):
        """
        1, 店铺排名
        2, 推广状况
        :param cover_days: 覆盖更新的天数(更新:由于拿不到历史数据，cover_days统一设置成1)
        :return:
        """
        cover_days = 1
        print('开始更新店铺排名和推广状况, time: {}'.format(Date.now().format()))
        cookies = CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM, CookieData.CONST_USER_SYCM_BACKSTAGE[0][0])
        SycmPromAmount().set_cookies(cookies).entry()
        SycmShopRanMonitor(cookies).entry()
        print('更新店铺排名和推广状况结束')


if __name__ == '__main__':
    # Cron().save_goods_flow_sources_to_mysql(200)
    fire.Fire(Cron)
