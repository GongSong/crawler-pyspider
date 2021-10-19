from backstage_data_migrate.config import REDBOOK_GOODS_TYPE
from backstage_data_migrate.page.redbook_download_data_base import RedbookDownloadBase


class RedbookGoodsDown(RedbookDownloadBase):
    """
    小红书代购商家的 商品渠道 的流量表格下载
    """
    URL = 'https://ark.xiaohongshu.com/api/ark/chaos/trd/fetch/goods?type=1&fields=goods_name,country,barcode,c' \
          'reate_time,first_selling_date,last_selling_date,spu_id,goods_id,skucode,ipq,first_category_name,second_' \
          'category_name,third_category_name,forth_category_name,business_line,brand_name,buyable,in_stock_inventor' \
          'y,is_new_goods,price_pre_tax,price_post_tax,price_tax_amount,price_tax_rate,min_price_pre_tax_30d,min_pri' \
          'ce_post_tax_30d,strict_min_price_pre_tax_90d,strict_min_price_post_tax_90d,price_type,uv,pv,pv_uv_rate,wi' \
          'sh_list_user_cnt,wish_list_user_cnt_acc,add_cart_user_cnt,add_cart_user_cnt_acc,add_cart_goods_cnt,add_ca' \
          'rt_goods_cnt_acc,frequent_visitor,new_visitor,goods_up,rgmv,selling_cnt,up_uv_rate,rgmv_uv_rate,rgmv_up_r' \
          'ate,frequent_customers,new_customers&start_date={0}&end_date={0}&'

    def __init__(self, username, day):
        super(RedbookGoodsDown, self).__init__(self.URL, username, day, REDBOOK_GOODS_TYPE)
