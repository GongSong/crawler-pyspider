from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from hupun.page.base import *


class GoodsCategoryDelete(Base):
    """
    删除商品类目
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
     "name":"1",
     "op":"delete"
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

    def __init__(self, data, data_id, uid):
        """
        删除某个类目，即使该类目下有子类目，也会被删除;
        删除失败会报错，并返回错误信息;
        :param uid:
        """
        super(GoodsCategoryDelete, self).__init__()
        self.__uid = uid
        self.__data = data
        self.__data_id = data_id

    def get_request_data(self):
        return self.request_data % self.__uid

    def get_unique_define(self):
        return merge_str('goods_category_delete', self.__uid)

    def parse_response(self, response, task):
        # json 结果
        try:
            result = self.detect_xml_text(response.text)
            return {
                'msg': '已删除: {}'.format(self.__uid),
                # 'text': response.text,
                'parent_id': self.__uid,
            }
        except Exception as e:
            processor_logger.exception('删除 uid: {} 失败, error:{}'.format(self.__uid, e))
            # 发送失败的钉钉通知
            if Helper.in_project_env():
                title = '万里牛删除商品类目操作失败'
                content = '万里牛删除商品类目操作失败, 类目uid: {}'.format(self.__uid)
                self.crawl_handler_page(DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, content))
            # 发送失败的反馈
            return {
                'msg': '删除 uid: {} 失败'.format(self.__uid),
                # 'content': response.content,
                'uid': self.__uid,
            }
