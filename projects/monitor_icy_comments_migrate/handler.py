from monitor_icy_comments_migrate.model.barcode_es import BarcodeES
from monitor_icy_comments_migrate.page.catch_taobao_comments import CatchTaoBaoComments
from pyspider.helper.date import Date
from pyspider.libs.base_handler import *
from monitor_icy_comments_migrate.page.catch_jd_comments import CatchJDComments
from cookie.model.data import Data as CookieData


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    @every(minutes=24 * 60)
    def catch_jd_comments(self):
        all_jingdong_goods = BarcodeES().get_all_jingdong_goods()
        for _goods_id, _barcode in all_jingdong_goods:
            self.crawl_handler_page(CatchJDComments(_goods_id, _barcode))

    @every(minutes=50)
    def catch_taobao_comments(self):
        hour = int(Date.now().strftime('%H'))
        if hour == 22:
            processor_logger.info('到点了，开始抓取')
            self.crawl_handler_page(CatchTaoBaoComments(CookieData.CONST_USER_TAOBAO_BACK_COMMENT[0][0]))
        else:
            processor_logger.info('还没到点')
