from pyspider.core.model.mysql_base import *

"""
仓库服务的出入库单据信息
"""


class OrderInfo(Model):
    order_id = IntegerField(verbose_name='主键,订单ID', primary_key=True)
    type = IntegerField(verbose_name='订单类型')
    code = CharField(verbose_name='订单号')
    warehouse_id = IntegerField(verbose_name='仓库ID')
    count = IntegerField(verbose_name='发生数量')
    surplus_count = IntegerField(verbose_name='剩余数量')
    operator = IntegerField(verbose_name='(单据)提交人')
    submit_time = IntegerField(verbose_name='提交人的提交时间')
    related_order = CharField(verbose_name='一级关联单据')
    related_order_type = IntegerField(verbose_name='一级关联单据类型')
    related_sub_order = CharField(verbose_name='二级关联单据')
    shipment_code = CharField(verbose_name='物流单号')
    logistics_company = CharField(verbose_name='物流公司')
    create_time = IntegerField(verbose_name='创建时间')
    update_time = IntegerField(verbose_name='更新时间')

    class Meta:
        database = erp_db
        db_table = 'order_info'
