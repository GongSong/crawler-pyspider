import unittest

from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun_inventory.page.goods_inventory import GoodsInventory
from hupun_inventory.page.goods_inventory_jumper import GoodsInventoryJumper


class Test(unittest.TestCase):
    def test_inventory(self):
        """
        订单 的测试部分
        :return:
        """
        storage_ids = StoreHouse().get_storage_ids()
        GoodsInventory(storage_ids, False).set_priority(GoodsInventory.CONST_PRIORITY_FIRST).test()

    def test_inventory_jumper(self):
        """
        订单 的测试部分
        :return:
        """
        storage_ids = StoreHouse().get_storage_ids()
        GoodsInventoryJumper('CE62103B682739A5A2FDAA17E67774B3', storage_ids).test()
