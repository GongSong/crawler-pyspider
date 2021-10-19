from pyspider.core.model.mysql_base import *

"""
每天的sku单位成本备份
"""


class SkuDayDetail(Model):
    id = IntegerField(primary_key=True)
    back_up_day = IntegerField(verbose_name='备份日期，截止到当日24时静态数据')
    sku = CharField(verbose_name='skuBarCode')
    cost_price = DecimalField(verbose_name='单位成本')
    in_num = IntegerField(verbose_name='入库数')
    out_num = IntegerField(verbose_name='出库数')
    created_at = DateTimeField(verbose_name='创建时间')

    class Meta:
        database = xs_report_db
        db_table = 'sku_day_detail'
        indexes = (
            (('back_up_day', 'sku'), True),
        )
