from pyspider.core.model.mongo_base import *


class TianMao(Base):
    def __init__(self):
        super(TianMao, self).__init__('resultdb', 'tianmao')
