from pyspider.core.model.mysql_base import *

"""
线下的销售订单
"""


class OfflineOrder(Model):
    order_id = IntegerField(verbose_name='主键,订单号', primary_key=True)
    total_price = DecimalField(verbose_name='总支付金额')
    pay_time = IntegerField(verbose_name='支付时间')

    class Meta:
        database = retail_order_db
        db_table = 'order'
