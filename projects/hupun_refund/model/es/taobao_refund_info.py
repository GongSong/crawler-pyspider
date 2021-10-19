from pyspider.core.model.es_base import *


class TaobaoRefundInfo(Base):
    """
    万里牛 淘宝售后单 商品详情 的数据
    """

    def __init__(self):
        super(TaobaoRefundInfo, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_taobao_refund_info'
        self.test_index = 'pyhupun_taobao_refund_info_test'
        self.doc_type = 'data'
        self.primary_keys = 'combine_keys'
