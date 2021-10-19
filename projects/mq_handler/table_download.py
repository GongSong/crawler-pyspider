from mq_handler.base import Base


class TableDownload(Base):
    """
    文件下载 相关的 处理消息 部分
    """

    def execute(self):
        self.print_basic_info()
