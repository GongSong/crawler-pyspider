from crawl_taobao_goods_migrate.page.base_callback import BaseCallback


class GoodsCallback(BaseCallback):

    def __init__(self, url, name='goods_callback', priority=1):
        super(GoodsCallback, self).__init__(url, name, priority)
        """
        https://outertest.icy.design/internal.php?method=thirdparty.fetchGoods%26goodsId=585936072872%26platform=2%26fetchType=0
        http://icy.design/internal.php?method=thirdparty.fetchGoods&goodsId=592387601225&platform=2&fetchType=0
        """
