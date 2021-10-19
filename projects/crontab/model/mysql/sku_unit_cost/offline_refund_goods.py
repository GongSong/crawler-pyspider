from pyspider.core.model.mysql_base import *

"""
线下的退货订单商品
"""


class OfflineRefundGoods(Model):
    refund_order_goods_id = IntegerField(verbose_name='主键, 退货单商品自增id', primary_key=True)
    refund_id = CharField(verbose_name='退货单ID')
    order_id = CharField(verbose_name='原订单号')
    sku = CharField(verbose_name='sku货号')
    count = CharField(verbose_name='退货商品的数量')
    cash = DoubleField(verbose_name='现金退款')
    balance = DoubleField(verbose_name='账户余额退款')

    class Meta:
        database = retail_order_db
        db_table = 'refund_order_goods'
