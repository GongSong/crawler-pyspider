import json

from pyspider.core.model.es_base import *
from pyspider.helper import utils
from pyspider.helper.date import Date


class OrderGoods(Base):
    """
    万里牛订单商品
    """

    def __init__(self):
        super(OrderGoods, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_order_goods_v2'
        # self.test_index = 'pyhupun_order_goods_test'
        self.test_index = 'pyhupun_order_goods_v2'
        self.doc_type = 'data'
        self.primary_keys = ['sys_trade', 'sku_id', 'tp_tid']

    def clear_invalid(self, create_time, seconds=3600, max_count=10000):
        """
        清理无效的订单商品数据(合单拆到导致的多余数据)
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

    def new_clear_valid(self, max_count=5000, default_months=3):
        """
        新的删单逻辑
        :param max_count: 超过这个值，暂停删单
        :param default_months: 默认删近三个月的单
        :return:
        """
        print('新的删单逻辑')
        # 需要被删除的订单list
        delete_list = []
        clear_date = Date.now().plus_months(-default_months).to_month_start().format(full=False)
        print('clear_date', clear_date)
        # 按照每月的大小来逐步把订单查出来删掉, 防止es查询不全所有的订单
        for _ in Date.generator_date(clear_date, Date.now(), 'month'):
            # start 开始时间往前加一天确保可以覆盖每月
            start = Date(_).to_month_start().plus_days(-1).format(full=False)
            end = Date(_).to_month_end().format(full=False)

            all_query = EsQueryBuilder() \
                .range_gte('trade_create_time', start, end) \
                .aggs(EsAggsBuilder().terms('tp_oid_aggs', 'tp_oid', size=100000, min_doc_count=2)) \
                .search(self, 1, 0) \
                .get_aggregations()['tp_oid_aggs']['buckets']
            print('len all_query', len(all_query))
            for order in all_query:
                tp_oid = order['key']
                if not tp_oid:
                    continue
                # 查询tp_oid对应的订单
                query_order = EsQueryBuilder() \
                    .term('tp_oid', tp_oid) \
                    .add_sort('sync_time') \
                    .search(self, 1, 500).get_list()
                for index, _order in enumerate(query_order):
                    sys_trade = _order['sys_trade']
                    sku_id = _order['sku_id']
                    tp_tid = _order['tp_tid']
                    if index != 0:
                        delete_list.append((sys_trade, sku_id, tp_tid))

        count = len(delete_list)
        print('len delete list', count)
        if count <= 0:
            return
        if count > max_count:
            print('count/max_count: %s/%s' % (count, max_count))
            return
        for sys_trade, sku_id, tp_tid in delete_list:
            print(sys_trade, sku_id, tp_tid)
            delete_order = EsQueryBuilder() \
                .term('sys_trade', sys_trade) \
                .term('sku_id', sku_id) \
                .term('tp_tid', tp_tid)
            delete_order.delete_by_query(self)

    def new_clear_all(self, max_count=5000, default_years=2):
        """
        新的删除所有时间的重复订单逻辑
        :param max_count: 超过这个值，暂停删单
        :param default_years: 默认为2年
        :return:
        """
        print('新的删除所有时间的重复订单逻辑')
        # 需要被删除的订单list
        delete_list = []
        clear_date = Date.now().plus_months(-default_years * 12).to_month_start().format(full=False)
        print('clear_date', clear_date)
        # 一次性查出所有的重复订单
        start = clear_date
        end = Date.now().format(full=False)

        all_query = EsQueryBuilder() \
            .range_gte('trade_create_time', start, end) \
            .aggs(EsAggsBuilder().terms('tp_oid_aggs', 'tp_oid', size=100000, min_doc_count=2)) \
            .search(self, 1, 0) \
            .get_aggregations()['tp_oid_aggs']['buckets']
        print('len all_query', len(all_query))
        for order in all_query:
            tp_oid = order['key']
            if not tp_oid:
                continue
            # 查询tp_oid对应的订单
            query_order = EsQueryBuilder() \
                .term('tp_oid', tp_oid) \
                .add_sort('sync_time') \
                .search(self, 1, 500).get_list()
            for index, _order in enumerate(query_order):
                sys_trade = _order['sys_trade']
                sku_id = _order['sku_id']
                tp_tid = _order['tp_tid']
                if index != 0:
                    delete_list.append((sys_trade, sku_id, tp_tid))

        count = len(delete_list)
        print('len delete list', count)
        if count <= 0:
            return
        if count > max_count:
            print('count/max_count: %s/%s' % (count, max_count))
            return
        for sys_trade, sku_id, tp_tid in delete_list:
            print(sys_trade, sku_id, tp_tid)
            delete_order = EsQueryBuilder() \
                .term('sys_trade', sys_trade) \
                .term('sku_id', sku_id) \
                .term('tp_tid', tp_tid)
            delete_order.delete_by_query(self)
