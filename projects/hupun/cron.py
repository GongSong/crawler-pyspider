import fire
import time
from alarm.page.ding_talk import DingTalk
from hupun.config import *
from hupun.page.erp_goods_position.goods_position import GoodsPosition
from hupun_slow_crawl.model.es.goods_categories import GoodsCategories
from hupun.model.es.order import Order
from hupun.model.es.order_goods import OrderGoods
from hupun.model.es.purchase_order import PurchaseOrder
from hupun.model.es.purchase_order_close_msg import PurOrderCloseMsg
from hupun.model.es.purchase_order_goods import PurchaseOrderGoods
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun.page.in_sale_store_table.table_export import StatementExport
from hupun.page.purchase_store_order import PurchaseStoreOrder
from pyspider.helper.date import Date
from pyspider.helper.retry import Retry


class Cron:
    def clear(self, clear_all=False):
        """
        清理es已经更新成功的过期数据
        :param clear_all: 是否删除所有时间范围内的重复订单开关
        :return:
        """
        print('开始删单,{}'.format(Date.now().format()))
        if clear_all:
            OrderGoods().new_clear_all()
        else:
            OrderGoods().new_clear_valid()
        print('删单完成,{}'.format(Date.now().format()))

        # 订单和订单商品的删单逻辑
        # Order().clear_invalid(Date.now().plus_hours(-1), 1800)
        # OrderGoods().clear_invalid(Date.now().plus_hours(-1), 1800)

        # 由于抓取量太大，暂停近一个月的删单逻辑
        # Order().clear_invalid(Date.now().plus_days(-29), 12 * 3600)
        # OrderGoods().clear_invalid(Date.now().plus_days(-29), 12 * 3600)

        # Order().clear_invalid(Date.now().plus_days(-89), 48 * 3600)
        # OrderGoods().clear_invalid(Date.now().plus_days(-89), 48 * 3600)

    def clear_goods_categories(self):
        """
        清理商品类目的过期数据
        :return:
        """
        GoodsCategories().clear_invalid()

    def hitory_purchase_store_order(self, start_days, end_days, history=False):
        """
        获取采购入库单历史数据的脚本
        :param start_days:
        :param end_days:
        :param history:
        :return:
        """
        PurchaseStoreOrder.run_days(Date.now().plus_days(-start_days).to_day_start().format(),
                                    Date.now().plus_days(-end_days).to_day_end().format(), history=history)

    def purchase_order_close_check(self):
        """
        采购单关闭的兜底检查脚本
        :return:
        """
        all_close_pur = PurOrderCloseMsg().get_close_purchase_order()
        ding_msg = ''
        for _close_pur_list in all_close_pur:
            for _close_pur in _close_pur_list:
                # 未被检查的关闭采购单返回信息
                sku_barcode = _close_pur.get('sku_barcode')
                bill_code = _close_pur.get('bill_code')
                print('开始检查采购订单:{}的商品:{}'.format(bill_code, sku_barcode))
                print('close_goods_msg: {}'.format(_close_pur))

                # 查询采购订单商品的对应数据
                goods_msg = self._query_pur_order_goods(bill_code, sku_barcode)
                print('goods_msg: {}'.format(goods_msg))
                if goods_msg and isinstance(goods_msg, dict):
                    status, msg = self._compare_close_purchase(_close_pur, goods_msg)
                    if status == 1:
                        # 发送报警信息
                        warning_msg = '采购订单:{}的商品:{}对比有异常: {}, 请到线上及时检查。'.format(
                            bill_code, sku_barcode, ','.join(msg))
                        print(warning_msg)
                        ding_msg += warning_msg
                else:
                    # 发送报警信息
                    warning_msg = '未查询到采购订单:{}的商品:{}，请到线上及时检查。'.format(bill_code, sku_barcode)
                    ding_msg += warning_msg
                    print(warning_msg)
                # 发送更新采购单商品的查询状态
                data = {
                    'sku_barcode': sku_barcode,
                    'bill_code': bill_code,
                    'check_status': True,
                }
                print('检查采购订单:{}的商品:{}完成,更改该商品的检查状态'.format(bill_code, sku_barcode))
                PurOrderCloseMsg().update([data], async=True)
        if ding_msg:
            title = '关闭采购订单的校验程序警告'
            DingTalk(ROBOT_TOKEN, title, ding_msg).enqueue()

    def in_sale_store_table_export(self, start_day, end_day):
        """
        进销存报表下载
        :param start_day: 开始的日期，例：2 为前天
        :param end_day: 结束的日期，例：1 为昨天
        :return:
        """
        print('start_day', start_day)
        print('end_day', end_day)
        print('开始进销存报表下载: {}'.format(Date.now().format()))
        storage_ids = StoreHouse().get_storage_ids()
        storage_uids = ','.join(storage_ids) + ','
        for day in range(end_day, start_day + 1):
            StatementExport(storage_uids) \
                .set_start_time(Date.now().plus_days(-day).format()) \
                .set_end_time(Date.now().plus_days(-day).format()) \
                .set_cookie_position(1) \
                .set_priority(StatementExport.CONST_PRIORITY_FIRST).enqueue()
        print('进销存报表下载完成: {}'.format(Date.now().format()))

    def _query_pur_order_goods(self, bill_code, barcode, retry=3):
        """
        从采购订单商品的es中查询相关数据
        :param bill_code: 采购订单商品的 bill_cod
        :param barcode: 采购订单商品的 barcode
        :param retry: 重试次数
        :return:
        """
        try:
            bill_uid = PurchaseOrder().get_details_by_barcode(bill_code)
            bill_uid = bill_uid.get('bill_uid')
            if not bill_uid:
                return None
            print('billuid: {}'.format(bill_uid))
            order_goods = PurchaseOrderGoods().get_details_by_uid(barcode, bill_uid)
            return_dict = dict()
            return_dict['arrive_count'] = int(order_goods['pchs_receive'])
            return_dict['purchase_count'] = int(order_goods['pchs_size'])
            return_dict['sku_barcode'] = order_goods['spec_code']
            return_dict['remark'] = order_goods['remark']
            return return_dict
        except Exception as e:
            print('query purchase order goods error: {}'.format(e))
            if retry > 0:
                return self._query_pur_order_goods(bill_code, barcode, retry - 1)
            return None

    def _compare_close_purchase(self, input_dict, crawl_sku_dict):
        """
        比较两个dict数据是否一样
        :param input_dict:
        :param crawl_sku_dict:
        :return:
        """
        lack_data = list()
        if input_dict['sku_barcode'] != crawl_sku_dict.get('sku_barcode'):
            lack_data.append('sku_barcode')
        if input_dict['purchase_count'] != int(crawl_sku_dict.get('purchase_count')):
            lack_data.append('purchase_count')
        if input_dict['arrive_count'] != int(crawl_sku_dict.get('arrive_count')):
            lack_data.append('arrive_count')
        if crawl_sku_dict['remark'] != REMARK:
            lack_data.append('关闭备注不匹配')
        if lack_data:
            return 1, lack_data
        else:
            return 0, ''

    def update_good_position(self):
        print('开始爬取仓位信息,{}'.format(Date.now().format()))
        current_page = 1
        total_page = 1
        try:
            while current_page <= total_page:
                res = self.goods_position(current_page)
                time.sleep(3)
                current_page += 1
                total_page = res[1]
            print('完成爬取仓位信息,{}'.format(Date.now().format()))
        except Exception as e:
            title = '更新总仓货位信息程序警告'
            msg = "更新总仓货位信息失败，{}".format(e)
            DingTalk(ROBOT_TOKEN, title, msg).enqueue()

    @Retry.retry_parameter(3, sleep_time=50)
    def goods_position(self, current_page):
        res = GoodsPosition(current_page).use_cookie_pool().get_result()
        if res:
            return res
        else:
            return False


if __name__ == '__main__':
    fire.Fire(Cron)
