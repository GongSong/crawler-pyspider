import unittest

from crawl_taobao_goods_migrate.model.es.es_based_spu_summary import EsBasedSpuSummary
from crawl_taobao_goods_migrate.model.result import Result
from crawl_taobao_goods_migrate.page.goods_callback import GoodsCallback
from crawl_taobao_goods_migrate.page.goods_rate import GoodsRate
from crawl_taobao_goods_migrate.page.goods_shelf_callback import GoodsShelfCallback
from crawl_taobao_goods_migrate.page.goods_details import GoodsDetails
from crawl_taobao_goods_migrate.page.goods_image import GoodsImage
from crawl_taobao_goods_migrate.page.goods_shelf import GoodsShelf
from crawl_taobao_goods_migrate.page.shop_callback import ShopCallback
from crawl_taobao_goods_migrate.page.shop_details import ShopDetails


class Test(unittest.TestCase):

    CALLBACK_LINK = 'https://www.baidu.com/'

    def _test_goods_callback(self):
        assert GoodsCallback(self.CALLBACK_LINK).test()

    def _test_shop_callback(self):
        assert ShopCallback(self.CALLBACK_LINK).test()

    def _test_goods_shelf_callback(self):
        assert GoodsShelfCallback(self.CALLBACK_LINK).test()

    def _test_goods_details(self):
        assert GoodsDetails('https://item.taobao.com/item.htm?id=524148951163').test()

    def _test_goods_image(self):
        assert GoodsImage('524148951163', user_proxy=True, save_dict={'test': 'test01'}).test(retry_limit=3)
        assert GoodsImage('524148951163', user_proxy=True, save_dict={'test': 'test01'},
                          callback_link=self.CALLBACK_LINK).test(retry_limit=3)

    def _test_goods_shelf(self):
        assert GoodsShelf('https://item.taobao.com/item.htm?id=524148951163').test()

    def _test_shop_details(self):
        assert ShopDetails('https://shop151902390.taobao.com/').test()

    def _test_goods_rate(self):
        start_urls = [
            "//detail.tmall.com/item.htm?id=575708167637&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=596817367745&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=596272468625&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=564407552964&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=595318910445&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=592384865750&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=582567378513&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=593661725338&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=586236904178&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=584472262917&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=594563604679&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=566471999931&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=590193218211&rn=f601703215fe0a185af6781f22d0160e&abbucket=5",
            "//detail.tmall.com/item.htm?id=588740788597&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=594001443306&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=590094420663&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=588870853057&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=592717743699&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=592390773051&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=588654224892&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=587152243812&rn=f601703215fe0a185af6781f22d0160e",
            "//detail.tmall.com/item.htm?id=557614835934&rn=f601703215fe0a185af6781f22d0160e",
        ]
        for url in start_urls:
            assert GoodsRate(url).test()

    def test_es_list(self):
        Result().find_all_goods()


if __name__ == '__main__':
    unittest.main()
