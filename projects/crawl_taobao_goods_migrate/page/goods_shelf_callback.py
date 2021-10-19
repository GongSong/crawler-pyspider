from crawl_taobao_goods_migrate.page.base_callback import BaseCallback


class GoodsShelfCallback(BaseCallback):

    def __init__(self, url, name='goods_shelf_callback', priority=1):
        super(GoodsShelfCallback, self).__init__(url, name, priority)
