import copy

from hupun.page.base import *


class GoodsCategoryAppend(Base):
    """
    添加商品类目
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"remote-service",
   "service":"catagoryInterceptor#save",
   "supportsEntity":true,
   "parameter":{
     "uid":"%s",
     "parentid":"%s",
     "name":"%s",
     "op":"new",
     "sequence":0
   },
   "context":{},
   "loadedDataTypes":[
     "dtException",
     "ProductSpecExt",
     "dtMultiBarcode",
     "shop",
     "Unit",
     "dtWashingLable",
     "Catagory",
     "Goods",
     "Template",
     "Spec",
     "dtSupplier",
     "dtGoodsSupplier",
     "dtSelfUploadPic",
     "dtBarcode",
     "PrintConfig",
     "ProductBrandMulti",
     "dtSearch",
     "GoodsPermissions",
     "Storage",
     "dtErrorInfo",
     "storage",
     "dtManufacturer",
     "ProductBrand",
     "ProductSpecValue"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, data, data_id, uid, parent_id, name):
        """
        添加类目，parentid 和 uid 代表父级层级的ID，为 -1 则代表在顶级目录添加类目，否则添加在对应父ID的下级;
        不管传入参数正确与否，都不会返回错误信息
        :param uid:
        :param name:
        """
        super(GoodsCategoryAppend, self).__init__()
        self.__uid = uid
        self.__parent_id = parent_id
        self.__name = name
        self.__data_id = data_id
        self.__data = copy.deepcopy(data)

    def get_request_data(self):
        return self.request_data % (self.__uid, str(self.__parent_id), self.__name)

    def get_unique_define(self):
        return merge_str('goods_category_append', self.__uid, self.__parent_id, self.__name)

    def parse_response(self, response, task):
        from mq_handler import CONST_MESSAGE_TAG_CATEGORY_RESULT, CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        # json 结果
        result = self.detect_xml_text(response.text)
        erp_id = result['data']
        return_msg = {
            "code": 0,  # 0：成功 1：失败
            "errMsg": '',  # 如果code为1，请将失败的具体原因返回
            "systemTag": "ERP",  # 表示该消息从哪个系统发送，可选值有：AI 或 ERP
            "goodsCategoryId": self.__data.get('goodsCategoryId', ''),  # 天鸽类目id
            "erpGoodsCategoryId": erp_id,
            "name": self.__data.get('name', ''),
        }
        msg_tag = CONST_MESSAGE_TAG_CATEGORY_RESULT
        return_date = Date.now().format()
        MQ().publish_message(msg_tag, return_msg, self.__data_id, return_date, CONST_ACTION_UPDATE)
        return {
            # 'text': response.text,
            'uid': self.__uid,
            'parent_id': self.__parent_id,
            'operate_name': self.__name
        }
