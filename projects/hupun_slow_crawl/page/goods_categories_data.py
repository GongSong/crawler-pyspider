from hupun_slow_crawl.model.es.goods_categories import GoodsCategories as GoodsCateEs
from hupun.page.base import *


class GoodsCategoriesData(Base):
    """
    万里牛商品类目 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"catagoryInterceptor#getCatagories",
   "supportsEntity":true,
   "parameter":{
     "parentId":"%s",
     "isPackage":0
   },
   "sysParameter":{},
   "resultDataType":"v:goods.Goods$[Catagory]",
   "context":{},
   "loadedDataTypes":[
     "Goods",
     "Combination",
     "Spec",
     "dtManufacturer",
     "ProductBrandMulti",
     "shop",
     "GoodsPermissions",
     "dtGoodsSupplier",
     "PrintConfig",
     "Unit",
     "dtSelfUploadPic",
     "Template",
     "storage",
     "dtSearch",
     "dtBarcode",
     "dtBatchUnitCondition",
     "ProductBrand",
     "dtSupplier",
     "ProductSpecExt",
     "Catagory",
     "dtException",
     "dtMultiBarcode",
     "Storage",
     "dtErrorInfo",
     "dtWashingLable",
     "CombinationDetail",
     "ProductSpecValue"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, parent_id):
        super(GoodsCategoriesData, self).__init__()
        self.__parent_id = parent_id

    def get_request_data(self):
        return self.request_data % self.__parent_id

    def get_unique_define(self):
        return merge_str('goods_categories', self.__parent_id)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                _item['sync_time'] = sync_time
                uid = _item.get("uid")
                has_child = _item.get('hasChild')
                if has_child:
                    self.crawl_handler_page(GoodsCategoriesData(uid))
            # 这个异步更新数据需要开启 es 队列去消费
            GoodsCateEs().update(result['data'], async=True)
        return {
            'tag': '万里牛的商品类目',
            'parent_id': self.__parent_id,
            'length': len(response.content),
            'response': response.text,
        }
