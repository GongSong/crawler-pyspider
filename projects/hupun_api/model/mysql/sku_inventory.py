from pyspider.core.model.mysql_base import *

"""
万里牛库存sku数据的保存模块
"""


class SkuInventory(Model):
    goods_code = CharField(max_length=50, verbose_name='商品编码')
    lock_size = IntegerField(default=0, verbose_name='锁定库存')
    quantity = IntegerField(default=0, verbose_name='数量')
    sku_code = CharField(max_length=50, default='', verbose_name='规格编码')
    skc_code = CharField(max_length=50, default='', verbose_name='颜色编码')
    underway = IntegerField(default='', verbose_name='在途库存')
    update_time = DateTimeField(default=None, verbose_name='爬虫更新日期')
    storage_code = CharField(max_length=50, default='', verbose_name='仓库编码')

    class Meta:
        database = db
        db_table = 'spider_sku_inventory'
        # 设置索引
        indexes = (
            (('sku_code', 'storage_code'), True),
        )
