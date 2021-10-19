from pyspider.core.model.es_base import *


class SycmShopRanMonitorEs(Base):
    """
    生意参谋 获取排名前100的服装品牌店
    """

    def __init__(self):
        super(SycmShopRanMonitorEs, self).__init__()
        self.cli = es_cli
        self.index = 'crawler_sycm_shop_ranking_monitor'
        self.doc_type = 'data'
        self.primary_keys = ['date_type', 'type_begin_date', 'shop_name']
