import traceback
import fire
import time

from alarm.page.ding_talk import DingTalk
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun.page.purchase_order_goods_result import PurOrderGoodsResult
from hupun.page.purchase_order_result import PurchaseOrderResult
from hupun_inventory_details.config import ROBOT_TOKEN, WARNING_HOURS
from hupun_inventory_details.page.goods_inventory_details import GoodsInvDetails
from hupun_inventory_details.model.es.goods_inventory_details import GoodsInvDetails as GoodsInvDetailsEs
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger
from pyspider.helper.string import merge_str


class Cron:
    def goods_inventory_details(self, start_hours, end_hours, history=0):
        """
        出入库明细报表的商品库存状况 的数据；
        采购入库库存变更通知；
        :return:
        """
        storage_ids = StoreHouse().get_storage_ids()
        page = 1
        while True:
            print('解析第:{}页'.format(page))
            goods_data_obj = GoodsInvDetails(storage_ids, history). \
                set_start_time(Date.now().plus_hours(-start_hours).format()). \
                set_end_time(Date.now().plus_hours(-end_hours).format()). \
                set_priority(GoodsInvDetails.CONST_PRIORITY_FIRST). \
                set_page(page). \
                set_page_size(200). \
                set_cookie_position(1)
            data_status, data_result = CrawlerHelper().get_sync_result(goods_data_obj, delay_time=30)
            if data_status != 0:
                # 发送钉钉报警通知
                text = '本次采购入库库存变动数据获取失败，时间:{},错误信息:{}'.format(Date.now().format(), data_result)
                title = '采购入库库存变动数据获取失败'
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
                break
            if not data_result:
                print('没有第:{}页的数据，退出'.format(page))
                break

            for _goods in data_result:
                bill_code = _goods['billCode']
                erp_purchase_code = _goods['pchsBillCode']
                spec_code = _goods['specCode']
                size = _goods['size']
                quantity = _goods['quantity']
                if self._stockin_inv_in_redis(bill_code, spec_code, size, quantity) \
                    or GoodsInvDetailsEs().find_inventory_by_four_args(bill_code, spec_code, size, quantity):
                    continue
                else:
                    # 获取已入库数量
                    second_data = self._fetch_bill_data(erp_purchase_code)
                    bill_uid = second_data['bill_uid']
                    sku_data = self._fetch_purchase_sku(bill_uid)
                    in_store_num = 0
                    for _sku in sku_data:
                        if _sku['spec_code'] == spec_code:
                            in_store_num = _sku['pchs_receive']
                    if in_store_num == 0:
                        title = '采购订单入库有问题'
                        ding_msg = '采购订单:{}入库有问题,in_store_num为0, 对应的商品:{}'.format(erp_purchase_code, spec_code)
                        DingTalk(ROBOT_TOKEN, title, ding_msg).enqueue()
                        continue
                    # 发出采购库存变更通知
                    return_msg = {
                        "erpPurchaseNo": erp_purchase_code,  # erp采购单号
                        "changedNum": size,  # 变更的数量,可以为正负
                        "quantity": quantity,  # 库存结余
                        "skuBarcode": spec_code,  # sku
                        "inStoreNum": int(in_store_num)  # 已入库数量
                    }
                    data_id = erp_purchase_code
                    from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT
                    from mq_handler import CONST_ACTION_UPDATE
                    from pyspider.libs.mq import MQ
                    msg_tag = CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT
                    return_date = Date.now().format()
                    MQ().publish_message(msg_tag, return_msg, data_id, return_date, CONST_ACTION_UPDATE)
                    # 保存已经发送过入库通知的消息
                    self._save_stockin_inv(bill_code, spec_code, size, quantity)
            GoodsInvDetailsEs().update(data_result, async=True)
            page += 1

        # 检查数据并报警
        result = GoodsInvDetailsEs().get_last_sync_time()
        if result:
            max_sync_time = Date(int(result) / 1000)
            if max_sync_time < Date().now().plus_hours(-WARNING_HOURS):
                # 发送警报
                title = '万里牛的出入库明细报表的最后更新时间有异常.'
                text = '万里牛的出入库明细报表的最后更新时间有异常, 数据库的最后更新时间为:{}'.format(max_sync_time.format())
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
        else:
            # 发送警报
            title = '万里牛的出入库明细报表抓取有异常.'
            text = '万里牛的出入库明细报表抓取没有最后更新时间，有异常'
            DingTalk(ROBOT_TOKEN, title, text).enqueue()

    def fix_instore_data(self):
        """
        单个修复爬虫抓取入库数为0的bug
        :return:
        """
        # 获取已入库数量
        bill_code_list = ["CD201904250018"]
        spec_code_list = ["0000201(test01)"]
        for bill_code, spec_code in list(zip(bill_code_list, spec_code_list)):
            print(bill_code, spec_code)
            second_data = self._fetch_bill_data(bill_code)
            bill_uid = second_data['bill_uid']
            sku_data = self._fetch_purchase_sku(bill_uid)
            in_store_num = 0
            for _sku in sku_data:
                if _sku['spec_code'] == spec_code:
                    in_store_num = _sku['pchs_receive']
            if in_store_num == 0:
                print('error in_store_num: {}'.format(in_store_num))
                continue
            # 发出采购库存变更通知
            return_msg = {
                "erpPurchaseNo": bill_code,  # erp采购单号
                "changedNum": 0,  # 变更的数量,可以为正负
                "quantity": 0,  # 库存结余
                "skuBarcode": spec_code,  # sku
                "inStoreNum": int(in_store_num)  # 已入库数量
            }
            processor_logger.warning('return_msg: {}'.format(return_msg))
            data_id = bill_code
            from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT
            from mq_handler import CONST_ACTION_UPDATE
            from pyspider.libs.mq import MQ
            msg_tag = CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT
            return_date = Date.now().format()
            MQ().publish_message(msg_tag, return_msg, data_id, return_date, CONST_ACTION_UPDATE)

    def _fetch_bill_data(self, bill_code, retry=4):
        """
        基于单据编号返回对应的代购订单数据
        :param bill_code:
        :param retry:
        :return:
        """
        try:
            print('bill_code: {}'.format(bill_code))
            result = PurchaseOrderResult(bill_code) \
                .set_start_time(Date.now().plus_days(-90).format()) \
                .set_end_time(Date.now().format()) \
                .get_result()
            if result:
                return result
            else:
                return {}
        except Exception as e:
            print('err:{}, date:{}'.format(e, Date.now().format()))
            print(traceback.format_exc())
            if retry > 0:
                retry -= 1
                time.sleep(10)
                return self._fetch_bill_data(bill_code, retry)
            else:
                return {}

    def _fetch_purchase_sku(self, bill_uid, retry=4):
        """
        获取单条的采购单的sku数据
        :param bill_uid:
        :param retry:
        :return:
        """
        try:
            print('bill_uid: {}'.format(bill_uid))
            result = PurOrderGoodsResult(bill_uid).get_result()
            assert result, '没有抓取到采购单的sku数据'
            return result
        except Exception as e:
            print(e)
            if retry > 0:
                retry -= 1
                time.sleep(10)
                return self._fetch_purchase_sku(bill_uid, retry)
            else:
                return []

    def _stockin_inv_in_redis(self, bill_code, spec_code, size, quantity):
        """
        判断入库变动通知是否已经发送
        :param bill_code:
        :param spec_code:
        :param size:
        :param quantity:
        :return:
        """
        r_key = merge_str(bill_code, spec_code, size, quantity)
        result = default_storage_redis.get(r_key)
        if result:
            print('入库变动信息已经发送过了,bill_code:{},spec_code:{},size:{},quantity:{},时间:{}'.format(
                bill_code, spec_code, size, quantity, Date.now().format()))
        return True if result else False

    def _save_stockin_inv(self, bill_code, spec_code, size, quantity):
        """
        保存入库变动信息
        :param bill_code:
        :param spec_code:
        :param size:
        :param quantity:
        :return:
        """
        r_key = merge_str(bill_code, spec_code, size, quantity)
        r_value = 1
        r_exp = 3600 * 24 * 2
        default_storage_redis.set(r_key, r_value, r_exp)
        print('已保存入库变动信息到redis,bill_code:{},spec_code:{},size:{},quantity:{},时间:{}'.format(
            bill_code, spec_code, size, quantity, Date.now().format()))


if __name__ == '__main__':
    fire.Fire(Cron)
