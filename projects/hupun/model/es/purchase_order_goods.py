from pyspider.core.model.es_base import *


class PurchaseOrderGoods(Base):
    """
    万里牛 采购订单查看详情 的数据
    """

    def __init__(self):
        super(PurchaseOrderGoods, self).__init__()
        self.cli = es_cli
        self.index = 'hupun_purchase_goods_v2'
        self.test_index = 'pyhupun_purchase_goods_test'
        self.doc_type = 'data'
        self.primary_keys = 'detail_uid'

    def get_details_by_uid(self, barcode, bill_uid):
        """
        用 barcode 查询采购单商品数据
        :param barcode:
        :param bill_uid:
        :return:
        """
        query = EsQueryBuilder() \
            .term('spec_code', barcode) \
            .term('bill_uid', bill_uid) \
            .search(self, 1, 100) \
            .get_one()
        return query
