from hupun_inventory_details.page.whole_inout_order import WholeInoutOrder
from pyspider.helper.date import Date
from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    def crawl_whole_inout_order(self):
        self.crawl_handler_page(WholeInoutOrder(to_next_page=True)
                                .set_start_time(Date.now().plus_days(-30).format())
                                .set_end_time(Date.now().format()))

    def crawl_history_inout_order(self):
        # 爬取所有的历史数据
        self.crawl_handler_page(WholeInoutOrder(history=True, to_next_page=False)
                                .set_start_time(Date.now().plus_days(-365*3).format())
                                .set_end_time(Date.now().plus_days(-90).format()))
