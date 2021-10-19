import unittest
from monitor_shop_goods.page.shelf_tmall import ShelfTmall
from monitor_shop_goods.page.shelf_taobao import ShelfTaoBao
from monitor_shop_goods.page.shelf_jd import ShelfJD
from monitor_shop_goods.page.shelf_redbook import ShelfRedBook
from monitor_shop_goods.page.shelf_app import ShelfApp


class Test(unittest.TestCase):
    # 对上架、下架两种情况均进行测试
    def test_shelf_tmall(self):
        assert ShelfTmall('558513808703').test()

    def test_obtained_tmall(self):
        assert ShelfTmall('546381623094').test()

    def test_shelf_taobao(self):
        assert ShelfTaoBao('561399216343').test()

    def test_obtained_taobao(self):
        assert ShelfTaoBao('560693984168').test()

    def test_shelf_jd(self):
        assert ShelfJD('11147602457').test()

    def test_obtained_jd(self):
        assert ShelfJD('11015480697').test()

    def test_shelf_rb(self):
        assert ShelfRedBook('5a374c8270e752583bbbfc5c').test()

    def test_obtained_rb(self):
        assert ShelfRedBook('59fffc0e70e7522c7041a580').test()

    def test_shelf_app(self):
        assert ShelfApp('27021599158297257').test()

    def test_obtained_app(self):
        assert ShelfApp('27021599158291566').test()


if __name__ == '__main__':
    unittest.main()
