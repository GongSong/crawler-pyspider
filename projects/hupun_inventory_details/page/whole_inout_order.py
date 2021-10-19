from hupun.page.base import *
from mysql_async.page.mysql_bulk import MysqlBulk


class WholeInoutOrder(Base):
    """
    获取全部的出入库明细报表的 出入库明细;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"saleReportInterceptor#queryInventoryDetail",
   "supportsEntity":true,
   "parameter":{
     "type":null,
     "storageName":"-- 所有仓库 --",
     "order":"pism_time desc",
     "startDate":"%s",
     "startTime":"%s",
     "endDate":"%s",
     "endTime":"%s",
     "shops":"%s",
     "shopName":"",
     "customType":0,
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
    shops = "1F0A6974D35035079B2CA00BA4F84077,7F5259B8A03B37E686C00DD4E33562E5,D991C1F60CD5393F8DB19EADE17236F0," \
            "914E617DC96D3442BEC0B5E5844644BF,310CF8F1682B328E97C16F18C11EA713,216680CFCB953A858AB529BDBA940072," \
            "C9ACE29003EC3B9BB24D01FCFBBF6BE7,9A1C9BFF3C67302393D9BE60BB53B8EE,C91DC23F386A3A97BF61E2A673F20544," \
            "3CD4D2A1DA1E3011BAF3DB89B702AB11,608BDCA2F9A2335585996163B3FAD970,F2EE7675CB303A559D99CCD9128FCCC1," \
            "B5F7A1243389351588A1EA6AB03D9E85,F6DE93C932F639EF91C0C0C7D345667E,DCB7B3F969D53AE19DC25A0B667F769B," \
            "4FB19614A970319E90DBAD6642178918,394C4D37484B3521B02B1E929472DF17,"
    storage_uids = "D1E338D6015630E3AFF2440F3CBBAFAD,149273C58B8D312F8730DCE6EF8AB4EE,ABA16826CD14321ABA3FF3CAB7784D1D," \
                   "80323619B8C739F2B697F9CFD34C34AC,84EC790FC3A23E949DA0405D3D3D67D8,FD98F002BB663577937C87F392F68BF9," \
                   "B4E5BDD117F03E0F881CD6901713E7A4,1DE59E5DB146335DB473B7D261106184,21130C06EE723229AC379095BF0305A8," \
                   "AF744068E6143BF987A27248B7657428,7819177595E23AAF959A1A25357A23F0,DE64474B8C073511958B97BAF70F9558," \
                   "FBA807A72474376E8CFBBE9848F271B2,61071625A3CF3C3DB253ED30B3351DAB,DB87C7AB89BA3BA19D4611DF9776F6E7," \
                   "576274C6DF93368594AD31D2C803E7D5,56034EF88B003D17A290EA5C6276E722,E0380637D67638CCA94D81BF5FEDCC13," \
                   "F2166EDB63573C79A5F3DD8F9E240ED2,5E16BA6378D735AA9DAA2BF288EC07F5,FBF052D749AA3858B8882D3EFD1E29C3," \
                   "5094948ED5823B558DF5447D38241F34,9E92E974170130FD96578C930C3892E4,32515651648535419E1A9321F607107A," \
                   "6FFDF1FE9D313BB18061CA4B24EF8665,44FF14D20AA3343BB22D042DC68D3B6A,"

    def __init__(self, history=False, to_next_page=False):
        super(WholeInoutOrder, self).__init__()
        self.__unique_name = 'whole_inout_order'
        self.__history = history
        self.table_name = "online_stock_detail"
        self.__to_next_page = to_next_page

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
            start_date, start_time, end_date, end_time, self.shops, his, self.storage_uids,
            self._page_size, self._page)

    def get_unique_define(self):
        return merge_str(self.__unique_name, self._start_time, self._end_time, self._page_size, self._page)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text, handle=True)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
            MysqlBulk(self.table_name, result['data']['data']).enqueue()
            self.crawl_next_page()
        return {
            "response": response.text[:200],
            'page': self._page,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__to_next_page:
            self.crawl_handler_page(WholeInoutOrder(self.__history, self.__to_next_page).
                                    set_page(self._page + 1).
                                    set_page_size(self._page_size).
                                    set_start_time(self._start_time).
                                    set_end_time(self._end_time).
                                    set_priority(self._priority))
