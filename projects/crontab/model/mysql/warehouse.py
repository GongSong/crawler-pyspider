from pyspider.core.model.mysql_base import *

"""
仓库信息
"""


class Warehouse(Model):
    warehouse_id = IntegerField(verbose_name='主键, 仓库id', primary_key=True)
    type = IntegerField(verbose_name='类型, 例：门店仓')
    name = CharField(verbose_name='仓库名称')
    status = IntegerField(verbose_name='仓库状态')
    related_id = IntegerField(verbose_name='关联id,（shop_id）')
    create_time = IntegerField(verbose_name='创建时间')
    update_time = IntegerField(verbose_name='更新时间')

    class Meta:
        database = erp_db
        db_table = 'warehouse'
