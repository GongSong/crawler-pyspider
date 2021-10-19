from mq_handler.base import Base


class PurOrAdResult(Base):
    """
    添加采购订单 后返回的结果
    """

    def execute(self):
        print('添加采购订单返回的结果')
        self.print_basic_info()
