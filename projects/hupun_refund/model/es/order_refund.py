from pyspider.core.model.es_base import *


class OrderRefund(Base):
    """
    万里牛 商品售后单 的数据
    """

    def __init__(self):
        super(OrderRefund, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_order_refund'
        self.test_index = 'pyhupun_order_refund_test'
        self.doc_type = 'data'
        self.primary_keys = ['sys_shop', 'exchange_uid', 'exchange_no']
