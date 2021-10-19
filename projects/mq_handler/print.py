from mq_handler.base import Base


class Print(Base):
    def execute(self):
        self.print_basic_info()
