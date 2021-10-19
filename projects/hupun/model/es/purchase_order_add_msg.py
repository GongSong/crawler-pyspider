from pyspider.core.model.es_base import *


class PurOrderAddMsg(Base):
    """
    采购订单同步添加后，保存天鸽系统传过来的原始数据和新生成的采购单号
    """

    def __init__(self):
        super(PurOrderAddMsg, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_purchase_add_msg'
        self.test_index = 'pyhupun_purchase_add_msg_test'
        self.doc_type = 'data'
        self.primary_keys = 'bill_code'
