from pyspider.core.model.es_base import *
from pyspider.helper.date import Date



class MonitorSave2(Base):
    """
    监控所需的搜集数据存储
    """
    def __init__(self):
        super(MonitorSave2, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_monitor_save'
        self.test_index = 'pyhupun_monitor_save_test2'
        # self.test_index = 'pyhupun_orders_test'
        self.doc_type = 'data'
        self.primary_keys = ['project_name', 'inspection_item_name', 'normalized_insert_time']

    def get_last_normalized_insert_time(self):
        max_asyc_time = EsQueryBuilder() \
            .aggs(EsAggsBuilder().max('max_sync_time', 'normalized_insert_time')) \
            .search(self, 1, 0) \
            .get_aggregations()
        return max_asyc_time['max_sync_time']['value_as_string']
