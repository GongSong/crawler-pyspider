import unittest

from weipinhui_migrate.page.schedule_details import ScheduleDetails
from weipinhui_migrate.page.weipinhui import CatchWeipinhui
from pyspider.helper.date import Date


class Test(unittest.TestCase):
    def test_catch_weipinhui(self):
        begin_date = Date().now().plus_days(-1).format(full=False)
        end_date = begin_date
        assert CatchWeipinhui(begin_date, end_date, 1).test()

    def test_schedule_details(self):
        account = 'jie.xia@yourdream.cc'
        begin_date_day = Date.now().plus_days(-30).format(full=False)
        end_date_day = Date.now().plus_days(-1).format(full=False)
        begin_date_month = Date.now().to_month_start().format(full=False)
        end_date_month = Date.now().to_month_end().format(full=False)
        diff_type = [('近30天', 0, 'D', begin_date_day, end_date_day), ('月', 2, 'M', begin_date_month, end_date_month)]
        for save_type, date_mode, detail_type, begin_date, end_date in diff_type:
            ScheduleDetails(account, date_mode, detail_type, begin_date, end_date, save_type).test()


if __name__ == "__main__":
    unittest.main()
