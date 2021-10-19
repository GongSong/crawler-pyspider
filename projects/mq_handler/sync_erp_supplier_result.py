from mq_handler.base import Base


class SyncErpSupplierResult(Base):
    """
    同步 erp供应商数据 的结果
    """

    def execute(self):
        print('同步 erp供应商数据 的结果')
        self.print_basic_info()
