from hupun.page.base import *


class GoodsInvDetails(Base):
    """
    出入库明细报表的 采购入库 商品变化;
    只获取 采购入库 的出入库明细表数据;
    只能同步去拿商品的库存，不然没办法确定库存的变动
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"saleReportInterceptor#queryInventoryDetail",
   "supportsEntity":true,
   "parameter":{
     "type":6,
     "storageName":"-- 所有仓库 --",
     "order":"pism_time desc",
     "startDate":"%s",
     "startTime":"%s",
     "endDate":"%s",
     "endTime":"%s",
     "shops":"%s",
     "shopName":"",
     "customType":2,
     "days":"0",
     "his":%s,
     "costPers":true,
     "storageUid":"%s",
     "goods":null,
     "specCode":null,
     "typeName":"采购入库",
     "billCode":"",
     "tp_tid":"",
     "customerName":null,
     "customUid":null,
     "$dataType":"v:analyze.other.InventoryDetail$dtSearch"
   },
   "resultDataType":"v:analyze.other.InventoryDetail$[InventoryDetail]",
   "pageSize":"%d",
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "GoodsSpec",
     "MultiGroupShop",
     "dtSearch",
     "MultiStorageGroup",
     "Shop",
     "dtAsynCount",
     "InventoryDetail",
     "MultiShop",
     "dtSearchGoods",
     "GoodsPermissions"
   ]
 }
]]></request>
</batch>
"""
    shops = '1F0A6974D35035079B2CA00BA4F84077,7F5259B8A03B37E686C00DD4E33562E5,D991C1F60CD5393F8DB19EADE17236F0,' \
            '914E617DC96D3442BEC0B5E5844644BF,310CF8F1682B328E97C16F18C11EA713,216680CFCB953A858AB529BDBA940072,' \
            '62E10D70437E31EB94655C3D58324933,C9ACE29003EC3B9BB24D01FCFBBF6BE7,'

    def __init__(self, storage_ids, history=0):
        super(GoodsInvDetails, self).__init__()
        self.__storage_ids = storage_ids
        self.__storage_uids = ','.join(storage_ids) + ','
        self.__unique_name = 'goods_inventory_details'
        self.__history = history

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        start_time = '1980-01-01T' + Date(self._start_time).format_es_old_utc().split(
            'T', 1)[1] if self._start_time else '00:00:00Z'
        end_date = Date(self._end_time).to_day_start().format_es_old_utc() if self._end_time else \
            Date.now().to_day_start().format_es_old_utc()
        end_time = '1980-01-01T' + Date(self._end_time).format_es_old_utc().split(
            'T', 1)[1] if self._end_time else '23:59:00Z'
        his = 'false' if not self.__history else 'true'
        return self.request_data % (
            start_date, start_time, end_date, end_time, self.shops, his, self.__storage_uids,
            self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('goods_inventory_details', self._start_time, self._end_time, self._page_size, self._page)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
        return result['data']['data']
