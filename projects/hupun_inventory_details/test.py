import unittest

from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun_inventory_details.page.goods_inventory_details import GoodsInvDetails
from pyspider.helper.date import Date


class Test(unittest.TestCase):
    def test_inventory_details(self):
        """
        出入库明细报表的商品库存状况 的测试部分
        :return:
        """
        storage_ids = StoreHouse().get_storage_ids()
        start_hours = 2
        end_hours = 0
        GoodsInvDetails(storage_ids). \
            set_start_time(Date.now().plus_hours(-start_hours).format()). \
            set_end_time(Date.now().plus_hours(-end_hours).format()).test()

