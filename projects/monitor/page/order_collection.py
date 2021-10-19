from monitor.page.monitor_paras_collection_base import MonitorParasCollectionBase
from hupun.model.es.order import Order as EsOrder
from monitor.page.spiders.order_numbers_spider import OrderNums
from monitor.model.es.monitor_save2 import MonitorSave2


class OrderMonitorParasCollection(MonitorParasCollectionBase):
    '''
    收集订单监控所需的参数
    '''
    def __init__(self):
        super(OrderMonitorParasCollection, self).__init__()
        self.es_model = EsOrder
        self.spider = OrderNums
        self.save_es_model = MonitorSave2
        self.project_name = '订单爬虫'
        self.project_class = '万里牛'


if __name__ == '__main__':
    OrderMonitorParasCollection().status_aggregation()

