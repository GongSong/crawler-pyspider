from mq_handler.base import Base


class PurchaseWholeClResult(Base):
    """
    同步 采购单整单关闭 的结果
    """

    def execute(self):
        print('同步 采购单整单关闭 的结果')
        self.print_basic_info()
