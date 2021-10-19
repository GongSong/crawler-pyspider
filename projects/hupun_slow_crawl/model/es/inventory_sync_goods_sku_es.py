from pyspider.core.model.es_base import *


class InvSyncGoodsSkuEs(Base):
    """
    万里牛 库存同步商品sku 的数据
    """

    def __init__(self):
        super(InvSyncGoodsSkuEs, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_inventory_sync_goods_sku'
        self.test_index = 'pyhupun_inventory_sync_goods_sku_test'
        self.doc_type = 'data'
        self.primary_keys = 'spec_code'

    def get_all_inv_goods_sku(self, spec_code):
        """
        获取所有的库存同步商品数据
        :param spec_code: sku对应的spu
        :return:
        """
        return EsQueryBuilder() \
            .regexp('spec_code.keyword', '{}.*?'.format(spec_code)) \
            .search(self, 1, 200) \
            .get_list(False)
