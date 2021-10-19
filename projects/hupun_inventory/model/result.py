from pyspider.core.model.mongo_base import *


class HupunInventoryTask(Base):
    def __init__(self):
        super(HupunInventoryTask, self).__init__('taskdb', 'hupun_inventory')
