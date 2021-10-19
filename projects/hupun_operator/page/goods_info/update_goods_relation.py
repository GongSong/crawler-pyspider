import uuid

from hupun.page.base import *


class UpdateGoodsRe(Base):
    """
    更新商品的对应关系;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action":"remote-service",
  "service":"matchInterceptor#downloadItems",
  "supportsEntity":true,
  "parameter":{
    "status":3,
    "startDate":"%s",
    "endDate":"%s",
    "days":"30",
    "shopUid":"%s",
    "shopNick":"%s",
    "$dataType":"v:goods.match$dtDownload"
  },
  "context":{
  },
  "loadedDataTypes":[
    "dtCategory",
    "dtItem",
    "dtStore",
    "dtGoodsCombination",
    "dtDownload",
    "dtSearch",
    "Goods",
    "GoodsPermissions",
    "GoodsSpec"]
 }
]]></request>
</batch>
"""

    def __init__(self, shop_uid, shop_nick):
        super(UpdateGoodsRe, self).__init__()
        self.__shop_uid = shop_uid
        self.__shop_nick = shop_nick

    def get_request_data(self):
        start_time = Date(self._start_time).format_es_old_utc() if self._start_time \
            else Date().now().format_es_old_utc()
        end_time = Date(self._end_time).format_es_old_utc() if self._end_time else Date.now().format_es_old_utc()
        return self.request_data % (start_time, end_time, self.__shop_uid, self.__shop_nick)

    def get_unique_define(self):
        return merge_str('update_goods_relation', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return {
            'unique_name': 'update_goods_relation',
            'length': len(response.content),
            'response': result
        }
