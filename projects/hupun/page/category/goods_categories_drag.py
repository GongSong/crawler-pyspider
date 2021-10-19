from hupun.page.base import *


class GoodsCategoryDrag(Base):
    """
    拖拽改变商品类目层级关系
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"remote-service",
   "service":"catagoryInterceptor#dragCataTree",
   "supportsEntity":true,
   "parameter":{
     "sourceid":"%s",
     "sourcename":"%s",
     "parentid":"%s",
     "sequence":0
   },
   "context":{},
   "loadedDataTypes":[
     "Template",
     "Goods",
     "dtSearch",
     "dtBarcode",
     "dtSupplier",
     "ProductBrand",
     "PrintConfig",
     "dtGoodsSupplier",
     "dtException",
     "dtMultiBarcode",
     "dtErrorInfo",
     "Unit",
     "Spec",
     "storage",
     "ProductBrandMulti",
     "dtSelfUploadPic",
     "dtWashingLable",
     "dtManufacturer",
     "Storage",
     "Catagory",
     "ProductSpecExt",
     "GoodsPermissions",
     "shop",
     "ProductSpecValue"
   ]
 }
]]></request>
</batch>
    """

    def __init__(self, uid, parent_id, name):
        """
        拖拽类目;
        传入错误的参数发送请求后，返回的是正常的json数据，不会返回错误信息;
        传入错误的 name 参数不会影响拖拽操作，传入错误的 uid 或者 parent_id 会影响;
        :param uid: 代表被拖拽的类目ID,
        :param parent_id: 代表父级层级的ID，为 -1 则代表在顶级的类目;
        :param name:
        """
        super(GoodsCategoryDrag, self).__init__()
        self.__uid = uid
        self.__name = name
        self.__parent_id = parent_id

    def get_request_data(self):
        return self.request_data % (self.__uid, self.__name, self.__parent_id)

    def get_unique_define(self):
        return merge_str('goods_category_drag', self.__uid, self.__name, self.__parent_id)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        print(result)
        return {
            # 'text': response.text,
            'uid_id': self.__uid,
            'parent_id': self.__parent_id,
            'operate_name': self.__name
        }
