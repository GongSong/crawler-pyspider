from pyspider.core.model.es_base import *


class OrderRefundInfo(Base):
    """
    万里牛 商品售后单商品 的数据
    """

    def __init__(self):
        super(OrderRefundInfo, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_order_refund_info'
        self.test_index = 'pyhupun_order_refund_info_test'
        self.doc_type = 'data'
        self.primary_keys = 'combine_keys'
