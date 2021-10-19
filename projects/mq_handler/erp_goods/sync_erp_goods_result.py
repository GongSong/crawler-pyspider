from mq_handler.base import Base
from pyspider.helper.date import Date


class SyncErpGoodsResult(Base):
    """
    同步erp商品数据的结果
    """

    def execute(self):
        print('同步erp商品数据的结果')
        self.print_basic_info()
