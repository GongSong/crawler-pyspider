import uuid

from hupun.config import *
from hupun.page.base import *
from hupun.page.in_sale_store_table.export_file_download_req import ExportFileDownloadReq


class ExportTaskQuery(Base):
    """
    导出进销库存表的查询
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"documentInterceptor#queryExportTask",
   "supportsEntity":true,
   "parameter":{
     "startDate":"%s",
     "endDate":"%s",
     "$dataType":"dtExportTaskSearch"
   },
   "resultDataType":"v:downloadCalf$[dtExportTask]",
   "pageSize":%d,
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "dtExportTask",
     "dtExportType",
     "dtExportTaskSearch"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, compare_date, save_date_str, count, retry=0):
        super(ExportTaskQuery, self).__init__()
        self.__count = count
        self.__compare_date = compare_date
        self.__save_date_str = save_date_str
        self.__retry = retry

    def get_request_data(self):
        start_date = Date(self._start_time).now().format_es_old_utc() if self._start_time \
            else Date.now().format_es_old_utc()
        end_date = Date(self._end_time).now().format_es_old_utc() if self._end_time \
            else Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('in_sale_store_export_task_query', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']['data']
        export_flag = False
        # 处理状态
        for _r in result:
            export_type = _r.get('export_type')
            # 导出记录里的导出笔数
            count = _r.get('count')
            # 导出记录里的导出笔数
            url = _r.get('file_path')
            # 导出时间
            export_time = Date(_r.get('create_time')).timestamp()
            if export_type == STA_EXPORT_SUCCESS and int(count) == int(self.__count) and (
                export_time == self.__compare_date or export_time > self.__compare_date) and url:
                # 导出成功
                export_flag = True
                _r['$dataType'] = 'dtExportTask'
                _r['$entityId'] = '0'
                self.crawl_handler_page(
                    ExportFileDownloadReq(_r, self.__save_date_str)
                        .set_priority(ExportFileDownloadReq.CONST_PRIORITY_BUNDLED)
                        .set_cookie_position(1)
                )
        if not export_flag and self.__retry < STA_EXPORT_QUERY_TIMES:
            self.crawl_handler_page(
                ExportTaskQuery(self.__compare_date, self.__save_date_str, self.__count, self.__retry + 1)
                    .set_delay_seconds(self._delay_seconds)
                    .set_cookie_position(1)
                    .set_priority(self._priority))
        return {
            'unique_name': 'in_sale_store_export_task_query',
            # 'response': response.text,
            'retry': self.__retry,
            'export_flag': export_flag,
        }
