from alarm.page.ding_talk import DingTalk
from hupun.page.base import *
from hupun_inventory.config import ROBOT_TOKEN
from hupun_inventory.model.es.goods_inventory_sku import GoodsInventorySku


class GoodsInventoryChecker(Base):
    """
    库存状况 的sku级别的总数
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"remote-service",
   "service":"inventoryInterceptor#getInvTotalNum",
   "supportsEntity":true,
   "parameter":{
     "alarm":false,
     "canInit":false,
     "sortBy1":false,
     "nosize":false,
     "brandUids":"",
     "brandNames":"-- 所有品牌 --",
     "goodsType":0,
     "goodsTypeLable":"商品",
     "storageUids":"%s",
     "storageName":"-- 所有仓库 --",
     "storageType":"%s",
     "view":"inventory.info",
     "startQuantity":null,
     "endQuantity":null
   },
   "context":{},
   "loadedDataTypes":[
     "dtAsynCount",
     "GoodsSpec",
     "ProductBrandMulti",
     "Inventory",
     "WmsInventory",
     "Storage",
     "dtThirdStoInventory",
     "bill",
     "dtInvCondition",
     "Catagory",
     "MultiStorage",
     "GoodsPermissions",
     "InventoryChangeBillDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, storage_ids):
        super(GoodsInventoryChecker, self).__init__()
        self.__storage_ids = storage_ids
        self.__storage_uids = ','.join(storage_ids) + ','
        self.__storage_type = '0,' * len(storage_ids)

    def get_request_data(self):
        return self.request_data % (self.__storage_uids, self.__storage_type)

    def get_unique_define(self):
        return merge_str('goods_inventory_checker', self.__storage_uids, self.__storage_type)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        total_num = 0
        total_price = 0
        quantity_sum = 0
        rate = 0

        if len(result['data']):
            total_num = int(result['data']['totalNum'])
            total_price = float(result['data']['totalPrice'])

            # 比较es和万里牛的数量
            quantity_sum = int(GoodsInventorySku().get_word_sum('quantity'))
            diff_num = abs(total_num - quantity_sum)
            rate = diff_num / total_num
            if rate > 0.01:
                title = '万里牛库存数量异常报警'
                text = '万里牛的库存数量：{}，爬虫抓取入库的库存数量：{}，数量相差：{}，数据相差的数量比例：{}%'.format(
                    total_num, quantity_sum, diff_num, round(rate * 100, 2))
                self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))

        return {
            'unique_name': 'goods_inventory_checker',
            'text': response.text,
            'total_num': total_num,
            'quantity_sum': quantity_sum,
            'rate': rate,
            'total_price': total_price,
        }
