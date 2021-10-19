import unittest
from hupun_api.page.common_post import CommonPost
from hupun_api.page.goods import Goods
from hupun_api.page.inventory import InventoryApi
from hupun_api.page.order import OrderApi
from hupun_api.page.order_refund import OrderRefund
from hupun_api.page.purchase_order import PurchaseOrder
from hupun_api.page.purchase_order_add import PurchaseOrderAdd
from hupun_api.page.purchase_order_close import PurchaseOrderClose
from hupun_api.page.purchase_stockin_order.stockin_order_add import StockinOrderAdd
from hupun_api.page.purchase_stockin_order.stockin_order_query import StockinOrderQuery
from hupun_api.page.store_house import StoreHouse
from hupun_api.page.supplier import Supplier
from pyspider.helper.date import Date
from hupun_api.page.order_hm import OrderHm


class Test(unittest.TestCase):
    def _test_order_common(self):
        assert CommonPost('/erp/opentrade/query/trades') \
            .set_param('page', 1) \
            .set_param('limit', 10) \
            .set_param('modify_time', Date.now().plus_hours(-6).millisecond()) \
            .test()

    def _test_order_refund(self):
        """
        售后单
        :return:
        """
        page_no = 1
        page_size = 100
        result = OrderRefund() \
            .set_param('start_time', Date().now().plus_weeks(-1).millisecond()) \
            .set_param('end_time', Date().now().millisecond()) \
            .set_param('page', page_no) \
            .set_param('limit', page_size).get_result()
        print(result)

    def _test_goods(self):
        """
        商品信息
        :return:
        """
        page_no = 1
        page_size = 100
        result = Goods() \
            .set_param('page_no', page_no) \
            .set_param('page_size', page_size).get_result()
        print(result)

    def test_inventory_query(self):
        """
        库存的查询测试
        :return:
        """
        page_no = 1
        page_size = 100
        storage = '020'
        modify_time = Date.now().plus_hours(-1).millisecond()
        result = InventoryApi() \
            .set_param('storage', storage) \
            .set_param('modify_time', modify_time) \
            .set_param('page_no', page_no) \
            .set_param('page_size', page_size).get_result()
        print('result', result)

    def _test_purchase_order(self):
        """
        采购订单
        :return:
        """
        page_no = 1
        page_size = 10
        bill_code = 'CD201906040016'
        result = PurchaseOrder() \
            .set_param('bill_code', bill_code) \
            .set_param('page', page_no) \
            .set_param('limit', page_size).get_result()
        print(result)

    def _test_purchase_order_add(self):
        """
        采购订单新增
        :return:
        """
        js_data = {
            'storage_code': '020',
            'supplier_code': '0587',
            'remark': '接口测试',
            'details': [
                {
                    'price': 144.00,
                    'size': 5,
                    'spec_code': 'asdf3234',
                    'sum': 144 * 5,
                },
                {
                    'price': 14.00,
                    'size': 5,
                    'spec_code': 'asdf3234',
                    'sum': 144 * 5,
                }
            ]
        }
        result = PurchaseOrderAdd().set_param('bill', js_data).get_result()
        print('result: {}'.format(result))

    def _test_purchase_order_close(self):
        """
        采购订单关闭
        :return:
        """
        bill_code = 'CD201909020021'
        close_remark = '爬虫自己在执行过程中的关闭,不包含天鸽发起的关闭'
        result = PurchaseOrderClose() \
            .set_param('bill_code', bill_code) \
            .set_param('close_remark', close_remark) \
            .get_result()
        print('purchase order close result: {}'.format(result))

    def _test_purchase_stockin_order_query(self):
        """
        采购入库单API 的查询操作
        :return:
        """
        page_no = 1
        page_size = 100
        # bill_code = 'CG201903210011'
        modify_time = Date.now().plus_hours(-24).millisecond()
        result = StockinOrderQuery() \
            .set_param('modify_time', modify_time) \
            .set_param('page', page_no) \
            .set_param('limit', page_size).get_result()
        print('purchase store order: {}'.format(result))

    def _test_purchase_stockin_order_add(self):
        """
        采购入库单API 的添加操作
        :return:
        """
        send_data = {
            "storeHouseCode": "020",  # wln仓库编码
            "supplierCode": "0758",  # wln供应商编码
            "tgPurchaseBill": "TG2312340",  # 天鸽采购单号
            "erpPurchaseBill": "CD201907300004",  # erp采购单号
            "goodsList": [
                {
                    "skuBarcode": "1922A10009W703",  # 商品编码
                    "count": "2",  # 商品入库数量
                }
            ]
        }

        details = []
        for _data in send_data.get('goodsList'):
            inner_data = {
                'nums': int(_data.get('count')),
                'spec_code': _data.get('skuBarcode'),
                'pchs_bill_code': send_data.get('erpPurchaseBill')
            }
            details.append(inner_data)
        bill_date = Date.now().millisecond()
        js_data = {
            'bill_date': bill_date,
            'details': details,
            'storage_code': send_data.get('storeHouseCode'),
            'supplier_code': send_data.get('supplierCode'),
            'pchs_bill_code': send_data.get('erpPurchaseBill'),
            'remark': 'test..23',
        }
        result = StockinOrderAdd().set_param('bill', js_data).get_result()
        print('purchase store order add result: {}'.format(result))

    def _test_order(self):
        """
        订单
        :return:
        """
        start_page = 1
        page_size = 200
        modify_day = 90
        modify_time = Date.now().plus_days(-modify_day).to_day_end().millisecond()
        end_time = Date.now().plus_days(-modify_day + 1).to_day_start().millisecond()
        result = OrderApi() \
            .set_param('page', start_page) \
            .set_param('limit', page_size) \
            .set_param('modify_time', modify_time) \
            .set_param('end_time', end_time) \
            .get_result()
        print('result', result)

    def _test_order_by_time(self):
        """
        根据时间段查询订单
        :return:
        """
        page_no = 1
        page_size = 10
        modify_time = Date.now().plus_hours(-2).millisecond()
        result = OrderHm(to_next_page=True) \
            .set_param('modify_time', modify_time) \
            .set_param('page', page_no) \
            .set_param('limit', page_size).get_result()
        print(result)

    def _test_store_house(self):
        """
        仓库
        :return:
        """
        page_no = 1
        page_size = 10
        result = StoreHouse() \
            .set_param('page_no', page_no) \
            .set_param('page_size', page_size).get_result()
        print(result)

    def _test_supplier(self):
        """
        供应商
        :return:
        """
        page_no = 1
        page_size = 10
        result = Supplier() \
            .set_param('page_no', page_no) \
            .set_param('page_size', page_size).get_result()
        print(result)


if __name__ == '__main__':
    unittest.main()
