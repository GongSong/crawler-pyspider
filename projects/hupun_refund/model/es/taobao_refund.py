from pyspider.core.model.es_base import *


class TaobaoRefund(Base):
    """
    万里牛 淘宝售后单 的数据
    """

    def __init__(self):
        super(TaobaoRefund, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_taobao_refund'
        self.test_index = 'pyhupun_taobao_refund_test'
        self.doc_type = 'data'
        self.primary_keys = 'refund_no'
