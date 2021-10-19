from pyspider.core.model.es_base import *


class Weipinhui(Base):
    def __init__(self):
        super(Weipinhui, self).__init__()
        self.index = 'weipinhui_goods'
        self.test_index = 'weipinhui_goods_test'
        self.doc_type = 'data'
        self.primary_keys = ['logDate', 'goodsCode']
