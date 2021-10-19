from pyspider.core.model.mysql_base import *

"""
每天的线上库存备份
"""


class OnlineSkuDayStock(Model):
    id = IntegerField(primary_key=True)
    back_up_day = IntegerField(verbose_name='备份日期，截止到当日24时静态数据')
    sku = CharField(verbose_name='skuBarCode')
    storage_id = CharField(verbose_name='仓库ID')
    storage_name = CharField(verbose_name='仓库名字')
    actual_stock = IntegerField(verbose_name='实际库存')
    underway_stock = IntegerField(verbose_name='在途库存')
    lock_stock = IntegerField(verbose_name='锁定库存')
    available_stock = IntegerField(verbose_name='可用库存')
    created_at = DateTimeField(verbose_name='创建时间')

    class Meta:
        database = xs_report_db
        db_table = 'online_sku_day_stock'
        indexes = (
            (('back_up_day', 'sku', 'storage_id'), True),
        )
