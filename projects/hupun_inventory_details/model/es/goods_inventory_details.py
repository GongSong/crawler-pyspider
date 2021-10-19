from pyspider.core.model.es_base import *


class GoodsInvDetails(Base):
    """
    出入库明细报表的商品库存状况数据;
    只获取 采购入库 的出入库明细表数据;
    """

    def __init__(self):
        super(GoodsInvDetails, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_inventory_detail'
        self.test_index = 'pyhupun_inventory_detail_test'
        self.doc_type = 'data'
        self.primary_keys = ['billCode', 'specCode', 'size', 'quantity']

    def get_last_sync_time(self):
        max_asyc_time = EsQueryBuilder() \
            .aggs(EsAggsBuilder().max('max_sync_time', 'sync_time')) \
            .search(self, 1, 0) \
            .get_aggregations()
        return max_asyc_time['max_sync_time']['value']

    def find_inventory_by_four_args(self, billCode, specCode, size, quantity):
        """
        查找指定的商品库存
        :param billCode: 万里牛出入库单号
        :param specCode:
        :param size:
        :param quantity:
        :return:
        """
        data = EsQueryBuilder() \
            .term('billCode.keyword', billCode) \
            .term('specCode.keyword', specCode) \
            .term('size', size) \
            .term('quantity', quantity) \
            .search(self, 0, 1) \
            .get_one()
        return data
