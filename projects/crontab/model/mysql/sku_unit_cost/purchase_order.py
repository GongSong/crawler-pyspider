from pyspider.core.model.mysql_base import *

"""
采购入库单
"""


class PurchaseOrder(Model):
    warehouseOrderId = IntegerField(verbose_name='主键, 采购入库自增id', primary_key=True)
    purchaseId = IntegerField(verbose_name='采购单Id')
    submitTime = IntegerField(verbose_name='提交时间')

    class Meta:
        database = tg_common_db
        db_table = 'warehouse_order'
