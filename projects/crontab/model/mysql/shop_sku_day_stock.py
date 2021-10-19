from pyspider.core.model.mysql_base import *

"""
每天的门店库存备份
"""


class ShopSkuDayStock(Model):
    id = IntegerField(primary_key=True)
    back_up_day = IntegerField(verbose_name='备份日期，截止到当日24时静态数据')
    sku = CharField(verbose_name='skuBarCode')
    warehouse_id = IntegerField(verbose_name='仓库ID')
    shop_id = IntegerField(verbose_name='门店id')
    shop_type = IntegerField(verbose_name='0:直营, 1:加盟, 2:联营')
    actual_stock = IntegerField(verbose_name='实际库存')
    underway_stock = IntegerField(verbose_name='在途库存')
    lock_stock = IntegerField(verbose_name='锁定库存')
    available_stock = IntegerField(verbose_name='可用库存')
    created_at = DateTimeField(verbose_name='创建时间')

    class Meta:
        database = xs_report_db
        db_table = 'shop_sku_day_stock'
        indexes = (
            (('back_up_day', 'sku', 'warehouse_id'), True),
        )
