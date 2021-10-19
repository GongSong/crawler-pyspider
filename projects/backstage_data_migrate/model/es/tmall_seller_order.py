from pyspider.core.model.es_base import *


class TmallSellerOrderEs(Base):
    """
    天猫后台商家中心的近三个月订单交易数据 es
    """

    def __init__(self):
        super(TmallSellerOrderEs, self).__init__()
        self.cli = es_cli
        self.index = 'tmall_seller_orders'
        self.test_index = 'tmall_seller_orders_test'
        self.doc_type = 'data'
        self.primary_keys = ['order_id', 'goods_code']

    def find_goods_by_order_create_time(self, start_time, end_time):
        """
        根据 order_create_time 查询数据
        :param start_time: eg, 2019-06-02T23:47:27+08:00
        :param end_time:
        :return:
        """
        query_builder = EsQueryBuilder() \
            .range_gte('order_create_time', start_time, None) \
            .range_lte('order_create_time', None, end_time)
        return self.scroll(query_builder)

    def is_goods_in_db(self, goods_code, order_id):
        """
        判断商品是否已经被抓取了
        :param goods_code:
        :param order_id:
        :return:
        """
        query = EsQueryBuilder() \
            .term('goods_code.keyword', goods_code) \
            .term('order_id.keyword', order_id) \
            .search(self, 1, 1) \
            .get_one()
        if query:
            return True
        else:
            return False

    def get_last_update_time(self):
        """
        获取爬虫数据的最后更新时间;
        :return:
        """
        query = EsQueryBuilder() \
            .add_sort('sync_time') \
            .search(self, 1, 1) \
            .get_one()
        return query
