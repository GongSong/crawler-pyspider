import uuid

from hupun.page.base import *
from hupun_slow_crawl.model.es.shop_data import ShopData


class ShopCategories(Base):
    """
    这是库存同步的手动上传配置列表的内容;
    店铺信息也是从这里提取出来的;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"synPolicyInterceptor#querySynPolicy",
   "supportsEntity":true,
   "resultDataType":"v:inventory.sync$[SynPolicy]",
   "pageSize":0,
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
     "dtShop",
     "Catagory",
     "SynPolicy",
     "GoodsSpec",
     "Inventory",
     "WmsInventory",
     "Storage",
     "ProductBrandMulti",
     "bill",
     "dtInvCondition",
     "dtAsynCount",
     "dtThirdStoInventory",
     "MultiStorage",
     "GoodsPermissions",
     "InventoryChangeBillDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(ShopCategories, self).__init__()

    def get_request_data(self):
        return self.request_data

    def get_unique_define(self):
        return merge_str('shop_categories', uuid.uuid4())

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        save_data = []
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        for rst in result:
            save_dict = {}
            save_dict['shop_name'] = rst['shop_name']
            save_dict['shop_uid'] = rst['shop_uid']
            save_dict['show_name'] = rst['show_name']
            save_dict['shop_type'] = rst['shop_type']
            save_dict['shop_nick'] = rst['shop_nick']
            save_dict['sync_time'] = sync_time
            save_data.append(save_dict)
        save_data_after = [dict(t) for t in set([tuple(d.items()) for d in save_data])]
        ShopData().update(save_data_after, async=True)
        return {
            'unique_name': 'shop_categories',
            'length': len(response.content),
            'response': result
        }
