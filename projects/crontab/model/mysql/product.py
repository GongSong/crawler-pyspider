from pyspider.core.model.mysql_base import *

"""
仓库服务的库存信息
"""


class Product(Model):
    uid = IntegerField(verbose_name='主键,订单ID', primary_key=True)
    warehouse_id = IntegerField(verbose_name='仓库id')
    sku = CharField(verbose_name='sku barcode')
    spu = CharField(verbose_name='spu barcode')
    actual_stock = IntegerField(verbose_name='实际库存')
    underway_stock = IntegerField(verbose_name='在途库存')
    lock_stock = IntegerField(verbose_name='锁定库存')
    available_stock = IntegerField(verbose_name='可用库存')
    first_category_id = IntegerField(verbose_name='一级类目')
    second_category_id = IntegerField(verbose_name='二级类目')
    third_category_id = IntegerField(verbose_name='三级类目')
    submit_time = IntegerField(verbose_name='提交时间')
    create_time = IntegerField(verbose_name='创建时间')
    update_time = IntegerField(verbose_name='更新时间')

    class Meta:
        database = erp_db
        db_table = 'product'
