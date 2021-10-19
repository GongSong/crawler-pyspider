from pyspider.core.model.es_base import *


class EsTmallGoodsRate(Base):
    """
    天猫商品评价得分的数据
    """

    def __init__(self):
        super(EsTmallGoodsRate, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_tmall_goods_rate'
        self.test_index = 'pyhupun_tmall_goods_rate_test'
        self.doc_type = 'data'
        self.primary_keys = ['goods_sku', 'insert_date']
