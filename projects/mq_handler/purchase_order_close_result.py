from mq_handler.base import Base
from pyspider.helper.date import Date


class PurOrClResult(Base):
    """
    关闭采购订单 后返回的结果
    """

    def execute(self):
        print('关闭采购订单后返回的结果')
        self.print_basic_info()
