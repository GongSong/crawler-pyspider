from pyspider.core.model.mysql_base import *

"""
线下的销售订单商品
"""


class OfflineOrderGoods(Model):
    id = IntegerField(verbose_name='主键', primary_key=True)
    order_id = IntegerField(verbose_name='订单号')
    count = IntegerField(verbose_name='数量')
    final_price = DecimalField(verbose_name='最终支付金额')
    sku = CharField(verbose_name='sku')

    class Meta:
        database = retail_order_db
        db_table = 'order_goods'
