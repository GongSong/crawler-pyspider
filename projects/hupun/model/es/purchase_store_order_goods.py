from pyspider.core.model.es_base import *


class PurchaseStoreOrderGoods(Base):
    """
    万里牛 采购入库单详情
    """

    def __init__(self):
        super(PurchaseStoreOrderGoods, self).__init__()
        self.cli = es_cli
        self.index = 'hupun_purchase_store_order_goods'
        self.test_index = 'pyhupun_purchase_store_order_goods_test'
        self.doc_type = 'data'
        self.primary_keys = ['stock_detail_uid']
