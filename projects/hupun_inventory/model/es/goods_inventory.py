from pyspider.core.model.es_base import *
from pyspider.helper.date import Date


class GoodsInventory(Base):
    """
    库存状况下的数据
    """

    def __init__(self):
        super(GoodsInventory, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_goods_inventory'
        # self.test_index = 'pyhupun_goods_inventory_test'
        self.test_index = 'pyhupun_goods_inventory'
        self.doc_type = 'data'
        self.primary_keys = ['storageID', 'itemID']

    def clear_invalid(self, clear_time, seconds=3600, max_count=3000):
        """
        清理无效的库存数据
        :return:
        """
        max_sync_time = EsQueryBuilder() \
            .range_lte('sync_time', None, Date(clear_time).format_es_old_utc()) \
            .aggs(EsAggsBuilder().max('max_sync_time', 'sync_time')) \
            .search(self, 1, 0) \
            .get_aggregations()['max_sync_time']['value']
        if not max_sync_time:
            return
        query_builder = EsQueryBuilder().range_lte('sync_time', None, int(max_sync_time - seconds * 1000))
        count = query_builder.search(self, 1, 0).get_count()
        if count <= 0:
            return
        if count >= max_count:
            print('count/max_count: %s/%s' % (count, max_count))
            return
        result = query_builder.delete_by_query(self)
        print('delete inventory: deleted/total: {deleted}/{total}'.format(**result))
