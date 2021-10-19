from pyspider.core.model.mysql_base import *

"""
采购退货单
"""


class PurchaseRefund(Model):
    returnOrderId = IntegerField(verbose_name='主键', primary_key=True)
    submitTime = IntegerField(verbose_name='提交时间')

    class Meta:
        database = tg_common_db
        db_table = 'return_order'
