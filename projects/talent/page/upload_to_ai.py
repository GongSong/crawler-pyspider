import os
from pyspider.libs.base_crawl import *
from talent.page.test import Test
from alarm.page.ding_talk import DingTalk


class UploadToAi(BaseCrawl):
    URL = 'https://10.0.5.62/api/admin/talent/upload_taobaoke'

    # URL = 'http://192.168.4.86:5001/api/admin/talent/upload_taobaoke'

    def __init__(self, file_path):
        super(UploadToAi, self).__init__()
        self.__file_path = file_path

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.URL) \
            .set_task_id(md5string(self.__file_path)) \
            .set_headers_kv('Host', 'ai.ichuanyi.com') \
            .set_upload_files_kv('file', (os.path.basename(self.__file_path), oss.get_data(self.__file_path))) \
            .set_kwargs_kv('validate_cert', False)

    def parse_response(self, response, task):
        result = response.json
        error_names = result.get('error_names')
        token = 'cf333216cffbec68dc7f05a461523b854c21236e9c7b2f33129f0dd47d3d4cbe'
        title = 'AI后台的达人数据的每日报警'
        if error_names:
            self.crawl_handler_page(DingTalk(token, title, error_names))
        return {
            'result': result,
        }

    def result_hook(self, result, task):
        self.crawl_handler_page(Test())
