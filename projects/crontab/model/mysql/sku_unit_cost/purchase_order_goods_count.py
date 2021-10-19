from pyspider.core.model.mysql_base import *

"""
采购入库单商品的数量
"""


class PurchaseOrderGoodsCount(Model):
    warehouseSkuId = IntegerField(verbose_name='主键', primary_key=True)
    wareHouseId = IntegerField(verbose_name='入库表Id')
    skuId = IntegerField(verbose_name='skuId')
    wareHouseCount = IntegerField(verbose_name='入库数')
    onlineCount = IntegerField(verbose_name='线上数量')
    offlineCount = IntegerField(verbose_name='线下数量')

    class Meta:
        database = tg_common_db
        db_table = 'warehouse_sku'
