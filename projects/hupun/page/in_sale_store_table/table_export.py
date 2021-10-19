from hupun.config import *
from hupun.page.base import *
from hupun.page.in_sale_store_table.export_task_query import ExportTaskQuery


class StatementExport(Base):
    """
    进销存报表导出
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"remote-service",
   "service":"documentInterceptor#createTask",
   "supportsEntity":true,
   "parameter":{
     "condition":{
       "days":7,
       "startDate":"%s",
       "endDate":"%s",
       "view":"report.goods.report",
       "storage_uid":"",
       "storage_name":"-- 所有仓库 --",
       "isPackage":0,
       "his":false,
       "stockBillType":0,
       "topSale":0,
       "saleNumType":1,
       "reportType":"1",
       "noChangeInventory":false,
       "showAverageCost":false,
       "storage_uids":"%s",
       "detailStorage":true,
       "exportByItem":false
     },
     "exportType":7,
     "pageNo":1,
     "pageSize":20
   },
   "context":{},
   "loadedDataTypes":[
     "dtScmReport",
     "dtCondition",
     "MultiStorageGroup",
     "Catagory",
     "MultiStorage",
     "GoodsSpec",
     "GoodsPermissions"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, storage_uids):
        super(StatementExport, self).__init__()
        self.__storage_uids = storage_uids

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time \
            else Date.now().to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).to_day_start().format_es_old_utc() if self._end_time \
            else Date.now().to_day_start().format_es_old_utc()
        return self.request_data % (start_date, end_date, self.__storage_uids)

    def get_unique_define(self):
        return merge_str('in_sale_store_table_export', self._start_time)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        count = int(result['data']['count'])
        # 减一秒是为了确保比较的时间比万里牛的创建时间早一点点
        compare_date = Date.now().plus_seconds(-1).timestamp()
        save_date_str = Date(self._start_time).format(full=False) if self._start_time \
            else Date.now().plus_days(-1).format(full=False)
        self.crawl_handler_page(
            ExportTaskQuery(compare_date, save_date_str, count)
                .set_delay_seconds(STA_EXPORT_DELAY_TIME)
                .set_priority(ExportTaskQuery.CONST_PRIORITY_BUNDLED)
                .set_cookie_position(1)
        )
        return {
            'unique_name': 'in_sale_store_table_export',
            # 'response': response.text
        }
