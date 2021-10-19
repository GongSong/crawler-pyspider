from copy import deepcopy

from backstage_data_migrate.page.file_download.download_base import DownloadBase
from hupun.config import *
from hupun.page.base import *


class ExportFileDownloadReq(Base):
    """
    进销存报表下载以及保存
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"resolve-data",
   "dataResolver":"documentInterceptor#operTask",
   "dataItems":[
     {
       "alias":"dsExportTask",
       "data":{
         "$isWrapper":true,
         "$dataType":"v:downloadCalf$[dtExportTask]",
         "data":%s
       },
       "refreshMode":"value",
       "autoResetEntityState":true
     }
   ],
   "parameter":0,
   "context":{}
 }
]]></request>
</batch>
"""

    def __init__(self, data_dict, save_date_str):
        super(ExportFileDownloadReq, self).__init__()
        self.__data_dict = deepcopy(data_dict)
        self.__save_date_str = save_date_str

    def get_request_data(self):
        return self.request_data % json.dumps(self.__data_dict)

    def get_unique_define(self):
        return merge_str('in_sale_store_table_export_download_req', self.__save_date_str)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        download_url = result['returnValue']['data']['url']

        table_type = 'sheet'
        file_name = '[in_sale_form]{}.xlsx'.format(self.__save_date_str)
        file_path = oss.get_key(oss.CONST_IN_SALE_STORE_PATH, file_name)
        self.crawl_handler_page(
            DownloadBase(download_url)
                .set_table_type(table_type)
                .set_oss_path(file_path)
                .set_priority(CONS_CRAWL_BUNDLE)
                .set_file_size(4000)
        )
        return {
            'url': response.url,
            # 'response': response.content,
            'unique_name': 'in_sale_store_table_export_download_req',
        }
