from hupun.model.es.goods_sku import GoodsSku
from hupun.page.base import *


class GoodsInfoEditResult(Base):
    """
    同步获取万里牛 编辑商品信息 的页面数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"remote-service",
   "service":"goodsInterceptor#getSpecs",
   "supportsEntity":true,
   "parameter":{
     "goodsUid":"%s",
     "approveID": null,
     "status":"%d"
   },
   "sysParameter": {},
   "resultDataType": "v:goods.Goods$[Spec]",
   "pageSize": 1000,
   "context":{
     "switchContext": {}
   },
   "loadedDataTypes":[
    "dtActivityPrice",
    "shop",
    "dtSelfUploadPic",
    "dtErrorInfo",
    "dtSupplier",
    "Combination",
    "dtSameEncodingImportSwitch",
    "Storage",
    "PrintConfig",
    "GoodsPermissions",
    "ProductBrandMulti",
    "dtMultiBarcode",
    "storage",
    "ProductSpecExt",
    "dtException",
    "dtItem",
    "dtGoodsPrice",
    "dtBasicApproveLog",
    "Goods",
    "Spec",
    "dtGoodsCustomRate",
    "Unit",
    "dtSearch",
    "dtBarcode",
    "dtProductType",
    "ProductBrand",
    "dtBatchUnitCondition",
    "Template",
    "dtWashingLable",
    "dtManufacturer",
    "dtGoodsSupplier",
    "Catagory",
    "CombinationDetail",
    "ProductSpecValue"
  ]
}
]]></request>
</batch>
"""

    def __init__(self, goods_uid, status):
        """
        编辑商品信息 的页面数据
        :param goods_uid:
        :param status: 1, 启用中; 0, 停用中;
        """
        super(GoodsInfoEditResult, self).__init__()
        self.__goods_uid = goods_uid
        self.__status = status

    def get_request_data(self):
        return self.request_data % (self.__goods_uid, self.__status)

    def get_unique_define(self):
        return merge_str('goods_information_edit_result', self.__goods_uid, self.__status)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result['data']
