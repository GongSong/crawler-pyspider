from hupun_inventory.model.es.goods_inventory_sku import GoodsInventorySku as EsGoodsInventorySku
from monitor.page.monitor_paras_collection_base import MonitorParasCollectionBase
from monitor.page.spiders.inventory_goods_spiders import GoodsInventorySpider
from monitor.page.spiders.order_numbers_spider import OrderNums
from monitor.model.es.monitor_save2 import MonitorSave2
from pyspider.helper.date import Date, normalized_ctime


class InventoryMonitorParasCollection(MonitorParasCollectionBase):
    '''
    收集库存监控所需的参数
    '''

    def __init__(self):
        super(InventoryMonitorParasCollection, self).__init__()
        self.es_model = EsGoodsInventorySku
        self.spider = GoodsInventorySpider
        self.save_es_model = MonitorSave2
        self.project_name = '库存爬虫'
        self.project_class = '万里牛'


if __name__ == '__main__':
    InventoryMonitorParasCollection().status_aggregation()
