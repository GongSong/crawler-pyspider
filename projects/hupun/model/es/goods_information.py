from pyspider.core.model.es_base import *
from pyspider.helper.date import Date


class GoodsInformationEs(Base):
    """
    万里牛 商品信息 的数据
    """

    def __init__(self):
        super(GoodsInformationEs, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_goods'
        self.test_index = 'pyhupun_goods_test'
        self.doc_type = 'data'
        self.primary_keys = 'goodsCode'

    def get_all_goods(self, day_range=7):
        """
        获取所有的商品
        :param day_range: 获取近期的所有数据，默认是近7天
        :return:
        """
        query = EsQueryBuilder().range_gte('sync_time', Date.now().plus_days(-day_range).format_es_old_utc(), None)
        return self.scroll(query, page_size=20)
