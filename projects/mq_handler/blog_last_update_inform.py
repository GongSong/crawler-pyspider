from mq_handler.base import Base
from pyspider.helper.date import Date


class BlogUpInform(Base):
    """
    更新博客和 ins 之后的通知爬虫最后执行时间
    """

    def execute(self):
        print('更新博客和 ins 之后的通知爬虫最后执行时间')
        self.print_basic_info()
        # 写入数据
