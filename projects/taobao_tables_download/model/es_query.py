from pyspider.core.model.es_base import *


class GoodsEs(Base):
    def __init__(self):
        super(GoodsEs, self).__init__()
        self.index = 'ai_service_goods_data'
        self.doc_type = 'goods'
        self.primary_keys = ['goodsCode']

    def get_goods_by_channle(self, query_words):
        """
        获取不同渠道的所有商品
        :param query_words: 被获取的商品的渠道, 比如淘宝渠道，天猫渠道
        :return:
        """
        query_builder = EsQueryBuilder().exists(query_words)
        results = self.scroll(query_builder)
        return results
