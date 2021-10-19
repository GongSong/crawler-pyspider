from hupun_inventory_onsale.es.auto_shelf_switch import EsAutoShelfSwitch
from hupun_inventory_onsale.es.channel_shelf import EsChannelShelf
from hupun_inventory_onsale.es.es_sku_double_switch import EsSkuDoubleSwitch
from projects.hupun.page.base import *
from pyspider.helper.channel import erp_name_to_shopuid
from pyspider.helper.es_query_builder import EsQueryBuilder


class InventoryQuerySwitchStatus(Base):
    """
    获取库存订单的例外宝贝设置中 自动上架开关 的状态
    """
    request_data = """
        <batch>
        <request type="json"><![CDATA[{
        "action":"load-data","dataProvider":"matchInterceptor#queryItem","supportsEntity":true,
        "parameter":
        {"autoShelf":false,
        "item":"",
        "shopUid":"%s",
        "cateUid":null,"hasChild":true},
        "resultDataType":"v:inventory.item$[dtItem]",
        "pageSize":200,
        "pageNo":%d,
        "context":{},
        "loadedDataTypes":["dtCategory","dtItem","dtExpPolicy","dtSearch","ProductBrandMulti","dtInvCondition","GoodsSpec","Catagory","bill","MultiStorage","Storage","SynPolicy","dtAsynCount","dtThirdStoInventory","Inventory","dtShop","WmsInventory","GoodsPermissions","InventoryChangeBillDetail"]}
        ]]></request>
        </batch>
        """

    def __init__(self, channel, page_no, is_save=True):
        super(InventoryQuerySwitchStatus, self).__init__()
        self.__channel = channel
        self.__shop_uid = erp_name_to_shopuid(channel)
        self.__page_no = page_no
        self.__is_save = is_save

    def get_request_data(self):
        return self.request_data % (self.__shop_uid, self.__page_no)

    def get_unique_define(self):
        return merge_str('inventory_query_switch_status', self.__shop_uid, self.__page_no)

    def parse_response(self, response, task):
        result = self.detect_xml_text(response.text)
        if self.__is_save:
            data_list = []
            vip_data_list = []
            if len(result['data']['data']):
                for _item in result['data']['data']:
                    if _item['title'].startswith('秒') or \
                            "备用" in _item['title'] or "粉丝内购会" in _item['title'] or "直播" in _item['title']:
                        print('商品：{} 为秒杀款，过滤该商品'.format(_item['title']))
                        continue
                    item_id = _item.get('itemID')[2:]
                    outer_id = _item.get('outerID')
                    name = _item.get('title')
                    channel = self.__channel
                    sync_time = Date.now().format_es_utc_with_tz()
                    switch_status = '关' if _item.get('upload') == 0 or _item.get('upload') == 1 else '开'
                    inventory_switch_status = '关' if _item.get('upload') == 0 else '开'
                    if '唯品会' in self.__channel:
                        data = {
                            "fakeSku": outer_id,
                            "spuBarcode": outer_id[:-4],
                            "channelProductId": item_id,
                            "channel": channel,
                            "syncTime": sync_time,
                            "switchStatus": switch_status,
                            "name": name,
                            "inventorySwitchStatus": inventory_switch_status
                        }
                        vip_data = {
                            "skuBarcode": outer_id,
                            "spuBarcode": outer_id[:10],
                            "channel": channel,
                            "syncTime": sync_time,
                            "switchStatus": switch_status,
                            "name": name,
                            "inventorySwitchStatus": inventory_switch_status
                        }
                        vip_data_list.append(vip_data)
                    elif '小红书' in self.__channel:
                        outer_id = EsQueryBuilder().term('productId', item_id).search(EsChannelShelf(),1, 100).get_one().get('spuBarcode')
                        print(outer_id)
                        data = {
                            "fakeSku": item_id,
                            "spuBarcode": outer_id,
                            "channelProductId": item_id,
                            "channel": channel,
                            "syncTime": sync_time,
                            "switchStatus": switch_status,
                            "name": name,
                            "inventorySwitchStatus": inventory_switch_status
                        }
                    else:
                        data = {
                            "fakeSku": item_id,
                            "spuBarcode": outer_id,
                            "channelProductId": item_id,
                            "channel": channel,
                            "syncTime": sync_time,
                            "switchStatus": switch_status,
                            "name": name,
                            "inventorySwitchStatus": inventory_switch_status
                        }
                    data_list.append(data)
                # 打印过多的日志，暂停
                # print(data_list)
                EsAutoShelfSwitch().update(data_list, async=True)
                EsSkuDoubleSwitch().update(vip_data_list, async=True)
        return result
