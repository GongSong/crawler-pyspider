import unittest

from hupun.page.hupun_goods.goods_information import GoodsInformation
from hupun.page.hupun_goods.goods_information_sku import GoodsInformationsku
from hupun.page.in_sale_store_table.export_file_download_req import ExportFileDownloadReq
from hupun.page.in_sale_store_table.export_task_query import ExportTaskQuery
from hupun.page.in_sale_store_table.table_export import StatementExport
from hupun.page.order import Order
from hupun.page.order_goods import OrderGoods
from hupun.page.purchase_order import PurchaseOrder
from hupun.page.purchase_order_goods import PurchaseOrderGoods
from hupun.page.purchase_store_order import PurchaseStoreOrder
from hupun.page.purchase_store_order_goods import PurchaseStoreOrderGoods
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun.page.sync_module.choose_purchase_bill import ChoosePurBill
from hupun.page.sync_module.choose_purchase_bill_sku import ChoosePurBillSku
from hupun.page.sync_module.confirm_purchase_stock import ConfirmPurBillStock
from hupun.page.sync_module.get_purchase_stock_token import PurchaseStockToken
from hupun.page.sync_module.submit_purchase_stock import SubmitPurBillStock
from pyspider.helper.date import Date


class Test(unittest.TestCase):
    def _test_order(self):
        """
        订单 的测试部分
        :return:
        """
        Order(True) \
            .set_start_time(Date.now().plus_days(-1).to_day_start().format()) \
            .set_end_time(Date.now().plus_days(-1).to_day_end().format()).test()
        Order(True) \
            .set_start_time(Date.now().plus_days(-120).to_day_start().format()) \
            .set_end_time(Date.now().plus_days(-120).to_day_end().format()).test()

    def _test_order_goods(self):
        """
        订单商品详情 的测试部分
        :return:
        """
        assert OrderGoods('A4380F4D6D153825AB891D632C341A45', 'D1E338D6015630E3AFF2440F3CBBAFAD',
                          'TB328906912208400576', '2019-01-17T02:49:20Z').test()

    def _test_purchase_order(self):
        """
        采购订单 的测试部分
        :return:
        """
        assert PurchaseOrder(True).set_start_time(Date.now().plus_days(-1).format()).test()

    def _test_purchase_order_goods(self):
        """
        采购订单查看详情 的测试部分
        :return:
        """
        assert PurchaseOrderGoods('189C28D94B3D390191F1DD1723F9544E').test()

    def _test_purchase_store_order(self):
        """
        采购入库单 的测试部分
        :return:
        """
        assert PurchaseStoreOrder(True).set_start_time(Date.now().to_day_start().format()).test()

    def _test_purchase_store_order_goods(self):
        """
        采购入库单查看详情数据 的测试部分
        :return:
        """
        assert PurchaseStoreOrderGoods('35414A5328FD3F66B3279E1ACC1E5E47').test()

    def _test_statement_export(self):
        """
        进销存表报导出 的单元测试
        :return:
        """
        storage_ids = StoreHouse().get_storage_ids()
        storage_uids = ','.join(storage_ids) + ','
        StatementExport(storage_uids).set_start_time(Date.now().plus_days(-1).format()).set_end_time(
            Date.now().plus_days(-1).format()).test()

    def _test_statement_task_query(self):
        """
        进销存报表导出记录查询 的单元测试
        :return:
        """
        compare_date = Date.now()
        ExportTaskQuery(compare_date, 1462).set_start_time(Date.now().plus_days(-7).format()).set_end_time(
            Date.now().format()).set_delay_seconds(1).test()

    def _test_statement_file_download(self):
        """
        进销存报表下载 的单元测试
        :return:
        """
        data = {
            "task_id": 3686347,
            "oper_uid": "9459514BF68F3C0A84343938A2CD7D75",
            "status": 2,
            "export_type": 7,
            "exportCaption": "进销存报表",
            "create_time": "2019-06-10T19:12:24Z",
            "download_time": "2019-06-11T12:02:50Z",
            "count": 1462,
            "download_times": 4,
            "oper_nick": None,
            "file_path": "export/excel/D1E338D6015630E3AFF2440F3CBBAFAD/进销存报表20190610191250_0(3686347).xlsx",
            '$dataType': 'dtExportTask',
            '$entityId': '0',
        }
        ExportFileDownloadReq(data).test()

    def _test_choose_purchase_bill(self):
        """
        采购入库单 的选择采购订单部分的采购订单详情 的单元测试
        :return:
        """
        bill_code = 'CD201905300017'
        storage_uid = 'FBA807A72474376E8CFBBE9848F271B2'
        storage_name = '研发测试仓'
        supplier_uid = 'EDF923722E993179829C929468693160'
        supplier_name = '测试777777'
        ChoosePurBill(bill_code, storage_uid, storage_name, supplier_uid, supplier_name) \
            .set_start_time(Date.now().plus_days(-60).format()) \
            .set_end_time(Date.now().format()) \
            .test()

    def _test_choose_purchase_bill_sku(self):
        """
        采购入库单 的选择采购订单部分的采购订单 商品详情 的单元测试
        :return:
        """
        bill_uid = '4E914B16058C3D02A42CE6479666A913'
        ChoosePurBillSku(bill_uid).test()

    def _test_submit_purchase_stock(self):
        """
        采购入库单 的提交入库变动的 的单元测试
        :return:
        """
        data = [
            {
                "goodsUid": "4AFB3148514C3FA99F332B05AAEC0A92",
                "goodsName": "测试--想念",
                "specUid": "1000577C001E3D14A8041BC5FD4CCDCE",
                "pic1": "http://test.image.yourdream.cc/ai-admin/ffa0d4ab8f89e8a6f79b0239f906a6b7.png",
                "specCode": "1919N00002W404",
                "specName": None,
                "unit_size": 1,
                "pchs_unit": None,
                "unit": None,
                "shouldNums": 87,
                "nums": 1,
                "discount_rate": 100,
                "price": 188,
                "pivtLast": 188,
                "primePrice": 188,
                "base_price": 188,
                "tax_rate": 0,
                "pchs_bill_uid": "483FAB78DF98341C8A7E0F16577E4F21",
                "pchs_bill_code": "CD201905300017",
                "appointBillType": 0,
                "pchs_detail_uid": "9DC3D695B16A3160BAEDD6E249B01C25",
                "pchs_detail_index": "10000",
                "remark": None,
                "openSN": 0,
                "expiration": None,
                "total_money": 188,
                "pay_type": None,
                "pchs_advance_balance": 18128,
                "stock_advance_balance": None,
                "settle_advance_balance": None,
                "tax": 0,
                "net_price": 188,
                "sn": None,
                "$dataType": "v:purchase.stock$dtStockBillDetail"
            },
            {
                "$dataType": "v:purchase.stock$dtStockBillDetail"
            }
        ]
        SubmitPurBillStock(data).test()

    def _test_confirm_purchase_bill_sku(self):
        """
        采购入库单 的选择采购订单部分的采购订单 商品详情 的单元测试
        :return:
        """
        token = PurchaseStockToken().get_result()
        ConfirmPurBillStock(token).test()

    def _test_get_purchase_stock_token(self):
        """
        采购入库单 的选择采购订单部分的采购订单 获取token 的单元测试
        :return:
        """
        PurchaseStockToken().test()

    def _test_get_goods_information(self):
        """
        商品信息 的单元测试
        :return:
        """
        GoodsInformation().test()

    def test_get_goods_information_sku(self):
        """
        商品信息sku 的单元测试
        :return:
        """
        goods_uid = 'C59933D09A893FDBB2FE8BB9BDD5E726'
        GoodsInformationsku(goods_uid).test()


if __name__ == '__main__':
    unittest.main()
