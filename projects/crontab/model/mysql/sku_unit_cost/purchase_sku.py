from pyspider.core.model.mysql_base import *

"""
采购库单的详情
"""


class PurchaseSku(Model):
    purchaseId = IntegerField(verbose_name='主键')
    skuId = IntegerField(verbose_name='主键')
    purchaseNum = IntegerField(verbose_name='采购数量')
    arriveCount = IntegerField(verbose_name='入库数量')
    finUntaxedPrice = DecimalField(verbose_name='不含税的单价')

    class Meta:
        database = tg_common_db
        db_table = 'purchase_sku'
        primary_key = CompositeKey('purchaseId', 'skuId')
