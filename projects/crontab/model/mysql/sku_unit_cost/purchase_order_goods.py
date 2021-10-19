from pyspider.core.model.mysql_base import *

"""
采购入库单商品的sku
"""


class PurchaseOrderGoods(Model):
    skuId = IntegerField(verbose_name='主键', primary_key=True)
    skuBarcode = CharField(verbose_name='skuBarcode')

    class Meta:
        database = tg_common_db
        db_table = 'goods_sku'
