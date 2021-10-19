from pyspider.core.model.es_base import *
from pyspider.helper.date import Date



class MonitorSave(Base):
    """
    监控所需的搜集数据存储
    """
    def __init__(self):
        super(MonitorSave, self).__init__()
        self.cli = es_cli
        self.index = 'pyhupun_monitor_save'
        self.test_index = 'pyhupun_monitor_save_test'
        # self.test_index = 'pyhupun_orders_test'
        self.doc_type = 'data'
        self.primary_keys = ['project_name', 'inspection_item_name', 'normalized_insert_time']




