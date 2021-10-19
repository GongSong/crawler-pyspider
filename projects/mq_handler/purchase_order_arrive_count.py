from mq_handler.base import Base
from pyspider.helper.date import Date


class PurOrArrCount(Base):
    """
    采购订单到仓数变动 后返回的结果
    """

    def execute(self):
        print('采购订单到仓数变动 后返回的结果')
        self.print_basic_info()
