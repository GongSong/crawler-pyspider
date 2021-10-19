from hupun.model.es.order import Order as EsOrder
from hupun_inventory.model.es.goods_inventory_sku import GoodsInventorySku
from monitor.model.es.monitor_save2 import MonitorSave2
from monitor.page.spiders.inventory_goods_spiders import GoodsInventorySpider
from monitor.page.spiders.order_numbers_spider import OrderNums
from pyspider.helper.date import Date
from pyspider.helper.es_query_builder import EsQueryBuilder


a = MonitorSave2().scroll(
                    EsQueryBuilder()
                    .range('normalized_insert_time', Date().now().plus_days(-1)
                    .format_es_old_utc(), None),
                        page_size=100
                    )
a_list = []
for _list in a:
    a_list.append(_list)
