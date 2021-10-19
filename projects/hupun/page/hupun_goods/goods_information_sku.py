from hupun.model.es.goods_sku import GoodsSku
from hupun.page.base import *


class GoodsInformationsku(Base):
    """
    万里牛 商品信息sku 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action": "load-data",
   "dataProvider": "goodsInterceptor#getSpecs",
   "supportsEntity": true,
   "parameter": {
     "status": "1",
     "goodsUid": "%s"
   },
   "resultDataType": "v:goods.Goods$[Spec]",
   "pageSize": 1000,
   "context": {},
   "sysParameter": {},
   "loadedDataTypes": [
     "Goods",
     "GoodsPermissions",
     "ProductBrandMulti",
     "dtBatchUnitCondition",
     "dtGoodsSupplier",
     "dtWashingLable",
     "dtMultiBarcode",
     "Spec",
     "dtSupplier",
     "Catagory",
     "dtManufacturer",
     "dtSelfUploadPic",
     "Storage",
     "Combination",
     "dtBarcode",
     "dtErrorInfo",
     "ProductBrand",
     "Unit",
     "PrintConfig",
     "storage",
     "ProductSpecExt",
     "dtException",
     "dtSearch",
     "Template",
     "shop",
     "ProductSpecValue",
     "CombinationDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, goods_uid):
        super(GoodsInformationsku, self).__init__()
        self.__goods_uid = goods_uid

    def get_request_data(self):
        return self.request_data % self.__goods_uid

    def get_unique_define(self):
        return merge_str('goods_information_sku', self.__goods_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
                if not _item.get('topGoodsCode', ''):
                    _item['topGoodsCode'] = _item['goodsCode'][:-4]
            # 这个异步更新数据需要开启 es 队列去消费
            GoodsSku().update(result['data']['data'], async=True)
        return {
            'tag': '万里牛的商品信息sku数据',
            'length': len(response.content),
            # 'response': response.text,
        }
