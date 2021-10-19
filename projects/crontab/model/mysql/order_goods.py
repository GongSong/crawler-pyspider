from pyspider.core.model.mysql_base import *

"""
仓库服务的出入库单据商品信息
"""


class OrderGoods(Model):
    uid = IntegerField(verbose_name='主键', primary_key=True)
    order_id = CharField(verbose_name='出入库ID')
    sku_id = CharField(verbose_name='关联skuid')
    count = IntegerField(verbose_name='入库数量')
    create_time = IntegerField(verbose_name='创建时间')
    surplus_count = IntegerField(verbose_name='剩余数量')

    class Meta:
        database = erp_db
        db_table = 'order_goods'
