from pyspider.core.model.es_base import *


class OrderRefundExchange(Base):
    """
    万里牛 商品售后换货单 的数据
    """

    def __init__(self):
        super(OrderRefundExchange, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_order_refund_exchange_info'
        self.test_index = 'pyhupun_order_refund_exchange_info_test'
        self.doc_type = 'data'
        self.primary_keys = 'combine_keys'
