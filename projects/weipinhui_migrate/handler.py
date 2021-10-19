from weipinhui_migrate.page.schedule_details import ScheduleDetails
from pyspider.libs.base_handler import *
from pyspider.helper.date import Date
from cookie.model.data import Data as CookieData
from weipinhui_migrate.page.weipinhui_file import WeipinhuiFile


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        pass

    @every(minutes=60 * 12)
    def catch_recent_days(self):
        for _i in range(1, 6):
            account, pwd = CookieData.CONST_USER_WEIPINHUI[0]
            begin_date = Date().now().plus_days(-_i).format(full=False)
            end_date = begin_date
            self.crawl_handler_page(WeipinhuiFile(account, begin_date, end_date))

    @every(minutes=60 * 24)
    def catch_recent_month(self):
        account, pwd = CookieData.CONST_USER_WEIPINHUI[0]
        for _i in range(1, 31):
            begin_date = Date().now().plus_days(-_i).format(full=False)
            end_date = begin_date
            self.crawl_handler_page(WeipinhuiFile(account, begin_date, end_date))

    @every(minutes=60 * 24)
    def catch_schedule_details(self):
        account = CookieData.CONST_USER_WEIPINHUI[0][0]
        begin_date_day = Date.now().plus_days(-30).format(full=False)
        end_date_day = Date.now().plus_days(-1).format(full=False)
        begin_date_month = Date.now().to_month_start().format(full=False)
        end_date_month = Date.now().to_month_end().format(full=False)
        diff_type = [('近30天', 0, 'D', begin_date_day, end_date_day), ('月', 2, 'M', begin_date_month, end_date_month)]
        for save_type, date_mode, detail_type, begin_date, end_date in diff_type:
            self.crawl_handler_page(
                ScheduleDetails(account, date_mode, detail_type, begin_date, end_date, save_type, catch_next_page=True))
