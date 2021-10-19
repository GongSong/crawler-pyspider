from pyspider.core.model.es_base import *


class PurchaseStoreOrder(Base):
    """
    万里牛 采购入库单
    """

    def __init__(self):
        super(PurchaseStoreOrder, self).__init__()
        self.cli = es_cli
        self.index = 'hupun_purchase_store_order'
        self.test_index = 'pyhupun_purchase_store_order_test'
        self.doc_type = 'data'
        self.primary_keys = 'stock_code'
