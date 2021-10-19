from pyspider.core.model.es_base import *


class SycmPromAmount(Base):
    """
    生意参谋 店铺 每日推广金额
    """

    def __init__(self):
        super(SycmPromAmount, self).__init__()
        self.cli = es_cli
        self.index = 'crawler_sycm_promotion_amount'
        self.doc_type = 'data'
        self.primary_keys = 'promotion_date'
