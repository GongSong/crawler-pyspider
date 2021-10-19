from pyspider.core.model.es_base import *


class SycmShopRanking(Base):
    """
    生意参谋 店铺 近30天支付金额排行
    """

    def __init__(self):
        super(SycmShopRanking, self).__init__()
        self.cli = es_cli
        self.index = 'crawler_sycm_shop_ranking'
        self.doc_type = 'data'
        self.primary_keys = 'ranking_date'
