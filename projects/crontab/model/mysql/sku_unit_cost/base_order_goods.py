from pyspider.core.model.mysql_base import *

"""
线上的商品销售信息
"""


class BaseOrderGoods(Model):
    id = IntegerField(verbose_name='主键', primary_key=True)
    order_id = CharField(verbose_name='订单号')
    sku = CharField(verbose_name='skuBarCode')
    sold_count = IntegerField(verbose_name='销售数量')
    paid_price = DecimalField(verbose_name='支付金额-总金额')
    paid_time = DateTimeField(verbose_name='支付时间')

    class Meta:
        database = xs_report_db
        db_table = 'based_order_goods'
        indexes = (
            (('order_id', 'sku'), True),
        )
