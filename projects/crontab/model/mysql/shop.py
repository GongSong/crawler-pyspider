from pyspider.core.model.mysql_base import *

"""
门店信息
"""


class Shop(Model):
    shop_id = IntegerField(verbose_name='店铺id', primary_key=True)
    shop_name = CharField(verbose_name='店铺名称')
    shop_type = IntegerField(verbose_name='店铺类型, 0:直营, 1:加盟, 2:联营')
    create_time = IntegerField(verbose_name='创建时间')
    update_time = IntegerField(verbose_name='更新时间')

    class Meta:
        database = erp_shop_db
        db_table = 'shop_info'
