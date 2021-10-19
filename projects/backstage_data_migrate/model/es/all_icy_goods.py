from pyspider.core.model.es_base import *


class AllIcyGoods(Base):
    """
    生意参谋 所有的icy商品 数据
    """
    page_size = 5000

    def __init__(self):
        super(AllIcyGoods, self).__init__()
        self.cli = es_cli
        self.index = 'based_spu_summary'
        self.doc_type = 'data'
        self.primary_keys = 'spuBarcode'

    def get_all_goods_id(self):
        """
        获取所有的商品ID, 不管是否上下架
        过滤商品ID为空的数据
        :return:
        """
        must_not_query = EsQueryBuilder().term("tmallGoodsId", "")
        query = EsQueryBuilder() \
            .exists('tmallGoodsId') \
            .must_not(must_not_query) \
            .source(['tmallGoodsId'])
        return self.scroll(query, page_size=self.page_size)
