from pyspider.core.model.es_base import *
from pyspider.helper.date import Date


class Order(Base):
    """
    trade_status: 0 审核中& 1 打单配货，2 验货& 13 配货中
    万里牛的订单
    """

    def __init__(self):
        super(Order, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_orders_v2'
        # self.test_index = 'pyhupun_orders_test'
        self.test_index = 'pyhupun_orders_v2'
        self.doc_type = 'data'
        self.primary_keys = 'salercpt_uid'

    def clear_invalid(self, create_time, seconds=3600, max_count=5000):
        """
        清理无效的订单数据(合单拆到导致的多余数据)
        :param create_time:
        :param seconds:
        :param max_count:
        :return:
        """
        max_sync_time = EsQueryBuilder() \
            .range_e('trade_create_time', Date(create_time).format_es_old_utc(), None) \
            .aggs(EsAggsBuilder().max('max_sync_time', 'sync_time')) \
            .search(self, 1, 0) \
            .get_aggregations()['max_sync_time']['value']
        if not max_sync_time:
            return
        query_builder = EsQueryBuilder() \
            .range_e('trade_create_time', Date(create_time).format_es_old_utc(), None) \
            .range('sync_time', None, int(max_sync_time - seconds * 1000))
        count = query_builder.search(self, 1, 0).get_count()
        if count <= 0:
            return
        if count > max_count:
            print('count/max_count: %s/%s' % (count, max_count))
            return
        result = query_builder.delete_by_query(self)
        print('delete order: deleted/total: {deleted}/{total}'.format(**result), )

    def get_es_numbers(self, start_day=0, end_day=0):
        start_time = Date.now().plus_days(-start_day).to_day_start().format_es_old_utc()
        end_time = Date.now().plus_days(-end_day).to_day_end().format_es_old_utc()
        # 收集es中的数量
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "trade_create_time": {
                                    "gte": start_time,
                                    "lte": end_time
                                }
                            }
                        }
                    ]
                }
            }
        }
        es_numbers = Order().search(query)['hits']['total']
        return es_numbers
