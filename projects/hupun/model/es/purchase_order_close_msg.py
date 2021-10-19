from pyspider.core.model.es_base import *


class PurOrderCloseMsg(Base):
    """
    采购订单同步关闭后，保存天鸽系统传过来的原始数据
    """

    def __init__(self):
        super(PurOrderCloseMsg, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_purchase_close_msg'
        self.test_index = 'pyhupun_purchase_close_msg_test'
        self.doc_type = 'data'
        self.primary_keys = ['sku_barcode', 'bill_code']

    def get_close_purchase_order(self, check_status=False):
        """
        获取未检测的所有数据
        :param check_status: True，已检查；False，未被检查
        :return:
        """
        query_builder = EsQueryBuilder() \
            .term('check_status', check_status) \
            .source(['bill_code', 'sku_barcode', 'purchase_count', 'arrive_count'])
        return self.scroll(query_builder)
