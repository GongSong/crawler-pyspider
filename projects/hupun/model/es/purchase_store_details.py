from pyspider.core.model.es_base import *


class PurchaseStoreDetails(Base):
    """
    万里牛 出入库明细报表的 采购入库 类型的数据
    """

    def __init__(self):
        super(PurchaseStoreDetails, self).__init__()
        self.cli = es_cli
        self.index = 'hupun_purchase_store_details'
        self.test_index = 'hupun_purchase_store_details_test'
        self.doc_type = 'data'
        self.primary_keys = ['billCode', 'specCode', 'size', 'quantity']
