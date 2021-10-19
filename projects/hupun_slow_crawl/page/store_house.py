from hupun.page.base import *
from hupun_slow_crawl.model.es.store_house import StoreHouse as StoreHouseEs


class StoreHouseP(Base):
    """
    仓库 标签的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"storageInterceptor#queryStorage",
   "supportsEntity":true,
   "parameter":{
     "storageCode":null,
     "storageName":null,
     "status":1
   },
   "resultDataType":"v:basic.Storage$[dtStorage]",
   "pageSize":%d,
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "dtSysThirdStorage",
     "dtThirdstorageConfig",
     "MultiShop",
     "dtThirdStorage",
     "dtPolicy",
     "dtStorage",
     "Storage",
     "dtCountry",
     "Region"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(StoreHouseP, self).__init__()

    def get_request_data(self):
        return self.request_data % (self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('store_house_data', self._page)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
                self.send_message(_item, merge_str('store_house_data', _item.get('storageUid', '')))
            StoreHouseEs().update(result['data']['data'], async=True)
        return {
            'text': response.text,
            'page': self._page,
        }
