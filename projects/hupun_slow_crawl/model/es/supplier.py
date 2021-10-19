from pyspider.core.model.es_base import *


class Supplier(Base):
    """
    万里牛 供应商信息 的数据
    """

    def __init__(self):
        super(Supplier, self).__init__()
        self.cli = es_cli
        self.index = 'hupun_supplier'
        self.test_index = 'pyhupun_supplier_test'
        self.doc_type = 'data'
        self.primary_keys = 'unitUid'

    def find_supplier_name_by_code(self, code):
        """
        通过code获取供应商的名称
        :param code:
        :return:
        """
        uid = EsQueryBuilder().term('unitCode.keyword', code).search(self, 1, 100).get_one()
        return uid.get('unitName')

    def find_supplier_uid_by_code(self, code):
        """
        通过code获取供应商的 uid
        :param code:
        :return:
        """
        uid = EsQueryBuilder().term('unitCode.keyword', code).search(self, 1, 100).get_one()
        return uid.get('unitUid')
