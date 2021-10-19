from hupun_slow_crawl.page.inv_sync_goods import InvSyncGoodsAll
from hupun_slow_crawl.page.shop_categories import ShopCategories
from pyspider.libs.base_handler import *
from hupun_slow_crawl.page.goods_categories_data import GoodsCategoriesData
from hupun_slow_crawl.page.store_house import StoreHouseP
from hupun_slow_crawl.page.supplier import Supplier


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    @every(minutes=60 * 24)
    def goods_categories(self):
        """
        每天更新一次 商品类目 的全量数据
        :return:
        """
        parent_id = '-1'
        self.crawl_handler_page(GoodsCategoriesData(parent_id))

    @every(minutes=60 * 12)
    def store_house(self):
        """
        每半天更新一次 仓库 的数据
        :return:
        """
        self.crawl_handler_page(StoreHouseP().set_priority(StoreHouseP.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 24)
    def supplier(self):
        """
        每天更新一次 供应商信息 的数据
        :return:
        """
        self.crawl_handler_page(Supplier(True).set_priority(Supplier.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 24)
    def shop(self):
        """
        每天更新一次 icy店铺信息 的数据
        :return:
        """
        self.crawl_handler_page(ShopCategories().set_priority(ShopCategories.CONST_PRIORITY_FIRST))

    @every(minutes=60 * 24)
    def inv_sync_goods(self):
        """
        每天更新一次 库存同步商品信息 全量抓取的数据
        :return:
        """
        self.crawl_handler_page(
            InvSyncGoodsAll(True)
                .set_priority(InvSyncGoodsAll.CONST_PRIORITY_FIRST)
                .set_page(1)
        )
