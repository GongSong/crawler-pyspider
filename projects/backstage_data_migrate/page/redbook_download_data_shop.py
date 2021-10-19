from backstage_data_migrate.config import REDBOOK_SHOP_TYPE
from backstage_data_migrate.page.redbook_download_data_base import RedbookDownloadBase


class RedbookShopDown(RedbookDownloadBase):
    """
    小红书代购商家的 店铺渠道 的流量表格下载
    """
    URL = 'https://ark.xiaohongshu.com/api/ark/chaos/trd/fetch/seller?type=1&fields=uv,pv,pv_uv_rate,wish_list_user_' \
          'cnt,wish_list_user_cnt_acc,add_cart_user_cnt,add_cart_user_cnt_acc,add_cart_goods_cnt,add_cart_goods_cnt_' \
          'acc,frequent_visitor,new_visitor,goods_up,rgmv,selling_cnt,up_uv_rate,rgmv_uv_rate,rgmv_up_rate,frequent_' \
          'customers,new_customers&start_date={0}&end_date={0}&'

    def __init__(self, username, day):
        super(RedbookShopDown, self).__init__(self.URL, username, day, REDBOOK_SHOP_TYPE)
