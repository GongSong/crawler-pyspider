from pyspider.core.model.es_base import *


class EsBasedSpuSummary(Base):
    """
    天猫商品评价得分的数据
    """

    def __init__(self):
        super(EsBasedSpuSummary, self).__init__()
        self.cli = es_cli
        self.index = 'based_spu_summary'
        self.test_index = 'based_spu_summary_test'
        self.doc_type = 'data'
        self.primary_keys = 'spuBarcode'
