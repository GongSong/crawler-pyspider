from pyspider.core.model.es_base import *


class GoodsSku(Base):
    """
    万里牛 商品信息sku 的数据
    """

    def __init__(self):
        super(GoodsSku, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_goods_sku'
        self.test_index = 'pyhupun_goods_sku_test'
        self.doc_type = 'data'
        self.primary_keys = 'goodsCode'

    def get_storage_ids(self):
        store_list = EsQueryBuilder().search(self, 1, 100).get_list()
        return [_['storageUid'] for _ in store_list]
