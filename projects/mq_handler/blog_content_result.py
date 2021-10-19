from mq_handler.base import Base
from pyspider.helper.date import Date


class BlogConResult(Base):
    """
    接收发送微博和 ins 的内容
    """

    def execute(self):
        print('接收发送微博和 ins 的内容')
        self.print_basic_info()
        # 写入数据
