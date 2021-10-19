from pyspider.core.model.es_base import *


class PurchaseOrder(Base):
    """
    万里牛 采购订单 的数据
    """

    def __init__(self):
        super(PurchaseOrder, self).__init__()
        self.cli = es_cli
        self.index = 'hupun_purchase_order_v2'
        self.test_index = 'pyhupun_purchase_order_test'
        self.doc_type = 'data'
        self.primary_keys = 'bill_uid'

    def get_details_by_barcode(self, bill_code):
        """
        用 barcode 查询采购单商品数据
        :param bill_code:
        :return:
        """
        query = EsQueryBuilder().term('bill_code', bill_code).search(self, 1, 100).get_one()
        return query
