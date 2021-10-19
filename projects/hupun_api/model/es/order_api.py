from pyspider.core.model.es_base import *


class OrderApiEs(Base):
    """
    万里牛 订单 的数据;
    从万里牛API获取;
    """

    def __init__(self):
        super(OrderApiEs, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_api_order'
        self.test_index = 'pyhupun_api_order_test'
        self.doc_type = 'data'
        self.primary_keys = 'trade_no'
