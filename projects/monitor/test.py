import unittest
from monitor.page.spiders.order_numbers_spider import OrderNums
from pyspider.helper.date import Date


class Test(unittest.TestCase):
    def test_order_nums(self):
        """
        订单 的测试部分
        :return:
        """
        OrderNums() \
            .set_start_time(Date.now().plus_days(-0).to_day_start().format()) \
            .set_end_time(Date.now().plus_days(-0).to_day_end().format()).test()


if __name__ == '__main__':
    unittest.main()
