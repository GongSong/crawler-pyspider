from pyspider.core.model.mysql_base import *

"""
采购退货单商品
"""


class PurchaseRefundGoods(Model):
    returnSkuId = IntegerField(verbose_name='主键', primary_key=True)
    returnOrderId = IntegerField(verbose_name='returnOrderId')
    purchaseId = IntegerField(verbose_name='采购单表Id')
    skuId = IntegerField(verbose_name='skuId')
    count = IntegerField(verbose_name='数量')

    class Meta:
        database = tg_common_db
        db_table = 'return_order_sku'
