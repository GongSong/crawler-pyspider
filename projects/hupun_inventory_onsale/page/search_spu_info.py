from projects.hupun.page.base import *
from pyspider.helper.channel import erp_name_to_shopuid


class SearchSpuInfo(Base):
    """
    库存订单同步例外宝贝设置中，获取宝贝信息
    """
    # 根据店铺和item查询，小红书的查询item为商品名。pigeSize由默认10改为50，避免翻页
    request_data = """
        <batch>
        <request type="json"><![CDATA[{
        "action":"load-data","dataProvider":"matchInterceptor#queryItem","supportsEntity":true,
        "parameter":
        {"autoShelf":false,
        "item":"%s",
        "shopUid":"%s",
        "cateUid":null,"hasChild":true},
        "resultDataType":"v:inventory.item$[dtItem]",
        "pageSize":50,
        "pageNo":1,
        "context":{},
        "loadedDataTypes":["dtCategory","dtItem","dtExpPolicy","dtSearch","ProductBrandMulti","dtInvCondition","GoodsSpec","Catagory","bill","MultiStorage","Storage","SynPolicy","dtAsynCount","dtThirdStoInventory","Inventory","dtShop","WmsInventory","GoodsPermissions","InventoryChangeBillDetail"]}
        ]]></request>
        </batch>
        """

    REDBOOK_SHOPNAME = "[小红书]ICY小红书"

    def __init__(self, item, shop_uid, outer_product_id=''):
        super(SearchSpuInfo, self).__init__()
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

            if len(result['data']['data']):
                for _item in result['data']['data']:
                    # title以'秒'字开头的商品是秒杀款，应过滤掉
                    if _item['title'].startswith('秒') or \
                            "备用" in _item['title'] or "粉丝内购会" in _item['title'] or "直播" in _item['title']:
                        print('商品：{} 为秒杀款，过滤该商品'.format(_item['title']))
                    elif self.__shop_uid == erp_name_to_shopuid(self.REDBOOK_SHOPNAME):
                        if not self.__outer_product_id:
                            print('小红书渠道查询时，必须含有小红书的outer_product_id')
                            return '查询小红书无outer_product_id'
                        if _item['itemID'] == self.__outer_product_id:
                            item_id = _item['itemID']
                            upload_status = _item['upload']
                            outer_id = _item['outerID']
                            item_list.append({'item_id': item_id, 'upload_status': upload_status, 'outer_id': outer_id})
                    else:
                        item_id = _item['itemID']
                        outer_id = _item['outerID']
                        sku_id = _item['skuID']
                        upload_status = _item['upload']
                        item_list.append({'item_id': item_id, 'upload_status': upload_status, 'sku_id': sku_id, 'outer_id': outer_id})
            return item_list


if __name__ == '__main__':
    a = SearchSpuInfo('0829L60010', 'D991C1F60CD5393F8DB19EADE17236F0', '').use_cookie_pool().get_result()
    print(a)
