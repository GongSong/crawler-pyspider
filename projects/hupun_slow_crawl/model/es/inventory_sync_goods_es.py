from pyspider.core.model.es_base import *
from pyspider.helper.date import Date


class InvSyncGoodsEs(Base):
    """
    万里牛 库存同步商品 的数据
    """

    def __init__(self):
        super(InvSyncGoodsEs, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_inventory_sync_goods'
        self.test_index = 'pyhupun_inventory_sync_goods_test'
        self.doc_type = 'data'
        self.primary_keys = 'spec_code'

    def get_all_inv_goods(self, day_range=7, page_size=20):
        """
        获取所有的库存同步商品数据
        :param day_range: 查询近段时间的数据, 默认为7天
        :param page_size: 返回的数量
        :return:
        """
        query = EsQueryBuilder().range_gte('sync_time', Date.now().plus_days(-day_range).format_es_old_utc(), None)
        return self.scroll(query, page_size=page_size)

    def get_single_inv_goods(self, spec_code):
        """
        获取单个库存同步的商品数据
        :param spec_code: spu号
        :return:
        """
        return EsQueryBuilder().term('spec_code.keyword', spec_code).search(self).get_one()
