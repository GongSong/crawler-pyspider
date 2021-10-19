from hupun_operator.page.upload_supplier import UploadSupplier
from mq_handler.base import Base


class SyncErpSupplier(Base):
    """
    同步 erp供应商的数据
    """

    def execute(self):
        print('同步erp供应商的数据')
        self.print_basic_info()
        UploadSupplier(self._data, self._data_id).enqueue()
