from mq_handler.base import Base
from pyspider.helper.date import Date


class CategoryResult(Base):
    """
    操作erp的类目数据的返回消息
    """

    def execute(self):
        print('category operation result data')
        self.print_basic_info()
        # 写入数据
        # UploadGoods(data, self._data_id).enqueue()
