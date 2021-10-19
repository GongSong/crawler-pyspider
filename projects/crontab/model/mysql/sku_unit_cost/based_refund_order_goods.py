from pyspider.core.model.mysql_base import *

"""
线上的商品退货信息
"""


class BaseRefundOrderGoods(Model):
    id = IntegerField(verbose_name='主键', primary_key=True)
    order_id = CharField(verbose_name='订单号')
    sku = CharField(verbose_name='skuBarCode')
    refund_count = IntegerField(verbose_name='退货数量')
    refund_price = DecimalField(verbose_name='退货金额')
    refund_time = DateTimeField(verbose_name='退货时间')

    class Meta:
        database = xs_report_db
        db_table = 'based_refund_order_goods'
        indexes = (
            (('order_id', 'sku'), True),
        )
