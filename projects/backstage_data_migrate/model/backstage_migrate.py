from pyspider.core.model.mongo_base import *


class Backstage(Base):
    def __init__(self):
        super(Backstage, self).__init__('resultdb', 'backstage_data_migrate')
