import unittest

from hupun_slow_crawl.model.es.goods_categories import GoodsCategories
from hupun_slow_crawl.page.store_house import StoreHouseP
from hupun_slow_crawl.page.supplier import Supplier


class Test(unittest.TestCase):
    def test_store_house(self):
        """
        仓库标签 的测试部分
        :return:
        """
        assert StoreHouseP().test()

    def test_get_goods_categories(self):
        """
        商品类目 的单元测试
        :return:
        """
        parent_id = '29378DA1C339316E95B0C039E87BCD07'
        name = '毛连衣裙'
        uid = ''
        # GoodsCategoriesData(parent_id).test()
        i = GoodsCategories().has_catetory(parent_id, name, uid)
        print('i', i)

    def test_supplier(self):
        """
        供应商信息 的测试部分
        :return:
        """
        assert Supplier(True).test()
