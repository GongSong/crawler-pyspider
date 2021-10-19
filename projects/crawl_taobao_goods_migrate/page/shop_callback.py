from crawl_taobao_goods_migrate.page.base_callback import BaseCallback


class ShopCallback(BaseCallback):

    def __init__(self, url, name='shop_callback', priority=1):
        super(ShopCallback, self).__init__(url, name, priority)
