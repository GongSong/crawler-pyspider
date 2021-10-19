from projects.hupun.page.base import *
from pyspider.helper.channel import erp_name_to_shopuid


class SearchSyncConfig(Base):
    """
    库存订单同步例外宝贝设置中，获取宝贝信息
    """
    # 根据店铺和item查询，小红书的查询item为商品名。pigeSize由默认10改为50，避免翻页
    request_data = """
<batch>
<request type="json"><![CDATA[
{"action":"load-data","dataProvider":"matchInterceptor#queryOlnSku","supportsEntity":true,
"parameter":{
"itemID":"%s",
"shopID":"%s"},
"sysParameter":{},"resultDataType":"v:inventory.item$[dtItem]","context":{},
"loadedDataTypes":["dtSearch","dtCategory","dtExpPolicy","dtItem","dtAsynCount","SynPolicy","dtShop","Inventory","Storage","dtInvCondition","Catagory","GoodsSpec","bill","WmsInventory","ProductBrandMulti","MultiStorage","dtThirdStoInventory","GoodsPermissions","InventoryChangeBillDetail"]}]]></request>
</batch>
        """

    REDBOOK_SHOPNAME = "[小红书]ICY小红书"

    def __init__(self, item, shop_uid, outer_product_id=''):
        super(SearchSyncConfig, self).__init__()
        self.__item = item
        self.__shop_uid = shop_uid
        self.__outer_product_id = outer_product_id

    def get_request_data(self):
        return self.request_data % (self.__item, self.__shop_uid)

    def get_unique_define(self):
        return merge_str('inventory_sync_config', self.__item, self.__shop_uid)

    def parse_response(self, response, task):
        if '会话过期' in response.text:
            return '会话过期'
        else:
            # print(response.text)
            result = self.detect_xml_text(response.text)
            item_list = []

            if len(result['data']):
                for _item in result['data']:
                    # title以'秒'字开头的商品是秒杀款，应过滤掉
                    if _item['title'].startswith('秒'):
                        print('商品：{} 为秒杀款，过滤该商品'.format(_item['title']))
                    elif self.__shop_uid == erp_name_to_shopuid(self.REDBOOK_SHOPNAME):
                        if not self.__outer_product_id:
                            print('小红书渠道查询时，必须含有小红书的outer_product_id')
                            return '查询小红书无outer_product_id'
                        if _item['itemID'] == self.__outer_product_id:
                            item_id = _item['itemID']
                            outer_id = _item['outerID']
                            sku_id = _item['skuID']
                            upload_status = _item['upload']
                            item_list.append({'item_id': item_id, 'upload_status': upload_status, 'sku_id': sku_id,
                                              'outer_id': outer_id})
                    else:
                        item_id = _item['itemID']
                        outer_id = _item['outerID']
                        sku_id = _item['skuID']
                        upload_status = _item['upload']
                        item_list.append({'item_id': item_id, 'upload_status': upload_status, 'sku_id': sku_id, 'outer_id': outer_id})
            return item_list


if __name__ == '__main__':
    a = SearchSyncConfig('TB584791541040', 'D991C1F60CD5393F8DB19EADE17236F0', '').set_cookie_position(2).get_result()
    print(a)
