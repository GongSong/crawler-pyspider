import uuid

from hupun.page.base import *
from hupun.page.hupun_goods.goods_information_sku import GoodsInformationsku


class GoodsInfoResult(Base):
    """
    根据「商品规格」在「万里牛商品信息」里查询商品数据;
    同步查询，返回查询到的结果;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "goodsInterceptor#queryGoods",
  "supportsEntity": true,
  "parameter": {
    "orderColumn": "goods_code",
    "orderSeq": "asc",
    "needCata": true,
    "status": "%d",
    "brands": "",
    "brandNames": "-- 所有品牌 --",
    "title": "",
    "hasChild": null,
    "isPackage": 0,
    "include_pkg": 1,
    "catagoryId": null,
    "sku": "%s",
    "$dataType": "v:goods.Goods$dtSearch"
  },
  "resultDataType": "v:goods.Goods$[Goods]",
  "pageSize": 20,
  "pageNo": 1,
  "context": {},
  "loadedDataTypes": [
    "Catagory",
    "ProductSpecExt",
    "storage",
    "dtMultiBarcode",
    "dtGoodsCustomRate",
    "dtActivityPrice",
    "dtProductType",
    "ProductBrandMulti",
    "Goods",
    "Template",
    "Storage",
    "dtSelfUploadPic",
    "dtManufacturer",
    "Combination",
    "dtException",
    "dtSupplier",
    "dtBatchUnitCondition",
    "dtGoodsPrice",
    "dtGoodsSupplier",
    "Spec",
    "dtBarcode",
    "shop",
    "dtErrorInfo",
    "GoodsPermissions",
    "dtSearch",
    "PrintConfig",
    "Unit",
    "dtWashingLable",
    "dtBasicApproveLog",
    "dtItem",
    "ProductBrand",
    "dtSameEncodingImportSwitch",
    "CombinationDetail",
    "ProductSpecValue"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, status, sku_barcode):
        """
        同步查询
        :param status: 1、启用中；0、停用中
        :param sku_barcode: 商品编码（万里牛里的商品规格）
        """
        super(GoodsInfoResult, self).__init__()
        self.__status = status
        self.__sku_barcode = sku_barcode

    def get_request_data(self):
        return self.request_data % (self.__status, self.__sku_barcode)

    def get_unique_define(self):
        return merge_str('goods_info_result', self.__status, self.__sku_barcode)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result['data']['data']
