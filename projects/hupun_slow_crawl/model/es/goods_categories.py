from pyspider.core.model.es_base import *
from pyspider.helper.date import Date


class GoodsCategories(Base):
    """
    万里牛的 商品类目
    """

    def __init__(self):
        super(GoodsCategories, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_goods_categories'
        self.test_index = 'pyhupun_goods_categories_test'
        self.doc_type = 'data'
        self.primary_keys = 'uid'

    def clear_invalid(self, seconds=3600 * 24 * 2, max_count=50):
        """
        清理无效的类目数据(类目增删导致的多余数据)
        :param seconds: 3天：3600 * 24 * 2
        :param max_count: 警戒删除数，在删除多余数据时，如果超过这个数，则代表有问题，立即暂停删除
        :return:
        """
        max_sync_time = EsQueryBuilder() \
            .aggs(EsAggsBuilder().max('max_sync_time', 'sync_time')) \
            .search(self, 1, 0) \
            .get_aggregations()['max_sync_time']['value']
        if not max_sync_time:
            return
        query_builder = EsQueryBuilder().range('sync_time', None, int(max_sync_time - seconds * 1000))
        count = query_builder.search(self, 1, 0).get_count()
        if count <= 0:
            return
        if count > max_count:
            print('count/max_count: %s/%s' % (count, max_count))
            return
        result = query_builder.delete_by_query(self)
        print('delete order: deleted/total: {deleted}/{total}'.format(**result), )

    def has_catetory(self, parent_id, name, uid):
        """
        判断类目是否在爬虫抓取到的数据库里
        :param parent_id: 类目的父ID
        :param name: 类目的名称
        :param uid: 类目的uid
        :return:
        """
        if uid:
            query_builder = EsQueryBuilder() \
                .term('uid.keyword', uid) \
                .term('catagoryName.keyword', name)
        else:
            query_builder = EsQueryBuilder() \
                .term('catagoryName.keyword', name)
        if parent_id:
            query_builder.term('parentid.keyword', parent_id)
        else:
            query_builder.must_not(EsQueryBuilder().exists('parentid.keyword'))
        result = query_builder.search(self, 1, 10).get_count()
        if result < 1:
            return False
        else:
            return True
