from pyspider.core.model.mysql_base import *

"""
线下的退货订单
"""


class OfflineRefund(Model):
    refund_order_id = IntegerField(verbose_name='主键, 退货单自增id', primary_key=True)
    refund_id = CharField(verbose_name='退货单ID, 系统生成')
    order_id = CharField(verbose_name='原订单号')
    cash = DoubleField(verbose_name='现金退款 -> 商品数量 * 商品单个现金退款')
    balance = DoubleField(verbose_name='账户余额退款 -> 商品数量 * 商品单个账户余额退款')
    refund_time = DateTimeField(verbose_name='退款时间')

    class Meta:
        database = retail_order_db
        db_table = 'refund_order'
