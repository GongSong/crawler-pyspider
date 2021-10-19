import uuid

from mysql_async.model.mysql.whole_inout_order import WholeInoutOrder
from mysql_async.page.data2model import whole_inout_order_transfer
from pyspider.libs.base_crawl import *


class MysqlBulk(BaseCrawl):
    def __init__(self, table_name: str, body: list):
        """
        批量写入MySQL
        :param body:
        """
        super(MysqlBulk, self).__init__()
        self.table_name = table_name
        self.body = body
        self.task_id = uuid.uuid4()

    def crawl_builder(self):
        return CrawlBuilder() \
            .schedule_retries(2) \
            .set_url("www.baidu.com#{}".format(self.table_name)) \
            .set_task_id(self.task_id)

    def parse_response(self, response, task):
        # 写入MySQL
        data_list = []
        if self.table_name == "online_stock_detail":
            # 线上的全部出入库明细 表
            data_list = whole_inout_order_transfer(self.body)
            if len(data_list) > 0:
                WholeInoutOrder.insert_many(data_list).on_conflict('replace').execute()
        return {
            'table_name': self.table_name,
            'data_list': len(data_list),
        }
