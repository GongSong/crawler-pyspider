from pyspider.core.model.es_base import *


class ShopData(Base):
    """
    万里牛 icy店铺信息 的数据
    """

    def __init__(self):
        super(ShopData, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_shop'
        self.test_index = 'pyhupun_shop_test'
        self.doc_type = 'data'
        self.primary_keys = 'shop_uid'

    def find_shop_by_name(self, shop_name):
        """
        根据店铺名返回shop_uid
        :param shop_name:
        :return:
        """
        uid = EsQueryBuilder().term('show_name.keyword', shop_name).search(self, 1, 100).get_one()
        return uid

    def find_shop_by_short_name(self, short_name):
        """
        根据shop_name查询店铺
        :param short_name:
        :return:
        """
        uid = EsQueryBuilder().term('shop_name.keyword', short_name).search(self, 1, 100).get_one()
        return uid
