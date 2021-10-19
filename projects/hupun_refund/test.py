from hupun_refund.page.order_refund import OrderRefund
from hupun_refund.page.order_refund_exchange_info import OrderRefundExchange
from hupun_refund.page.order_refund_info import OrderRefundInfo
from hupun_refund.page.order_refund_operation import OrderRefundOperation
from hupun_refund.page.taobao_refund import TaobaoRefund
from hupun_refund.page.taobao_refund_info import TaobaoRefundInfo
import unittest
from pyspider.helper.date import Date


class Test(unittest.TestCase):

    def test_taobao_refund(self):
        """
        淘宝售后单 的测试部分
        :return:
        """
        assert TaobaoRefund(True).test()

    def test_taobao_refund_info(self):
        """
        淘宝售后单商品详情 的测试部分
        :return:
        """
        assert TaobaoRefundInfo('TB372253376650582214', 'D991C1F60CD5393F8DB19EADE17236F0', 'TB21951041588581422',
                                'D1E338D6015630E3AFF2440F3CBBAFAD', 'SH201903130584', "0", '21951041588581422').test()

    def test_order_refund(self):
        """
        商品售后单 的测试部分
        :return:
        """
        assert OrderRefund(True).set_start_time(Date.now().format()).test()

    def test_order_refund_info(self):
        """
        商品售后单商品信息 的测试部分
        :return:
        """
        assert OrderRefundInfo('D991C1F60CD5393F8DB19EADE17236F0', 'A8FC5CE7D9853E2DACA1EF59F4BB8885',
                               'SH201903140886').test()

    def test_order_refund_exchange(self):
        """
        商品售后单订单 exchange 商品 的测试部分
        :return:
        """
        assert OrderRefundExchange('D991C1F60CD5393F8DB19EADE17236F0', 'A8FC5CE7D9853E2DACA1EF59F4BB8885',
                                   'SH201903140886').test()

    def test_order_refund_operation(self):
        """
        商品售后单 由于换货而新增的线下订单 的测试部分
        :return:
        """
        assert OrderRefundOperation('D991C1F60CD5393F8DB19EADE17236F0', 'A8FC5CE7D9853E2DACA1EF59F4BB8885',
                                    'SH201903140886').test()


if __name__ == '__main__':
    unittest.main()
