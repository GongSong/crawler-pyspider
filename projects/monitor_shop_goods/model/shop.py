from pyspider.core.model.mongo_base import *


class Shop(Base):
    def __init__(self):
        super(Shop, self).__init__('monitor_shop_goods_db', 'shop_goods')
