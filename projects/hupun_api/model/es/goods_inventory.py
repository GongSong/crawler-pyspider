from pyspider.core.model.es_base import *


class GoodsInventoryApi(Base):
    """
    库存状况 的数据
    """

    def __init__(self):
        super(GoodsInventoryApi, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_api_inventory'
        self.test_index = 'pyhupun_api_inventory_test'
        self.doc_type = 'data'
        self.primary_keys = ['goods_code', 'sku_code']
