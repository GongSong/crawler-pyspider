from pyspider.libs.base_crawl import *
from talent.page.upload_to_ai import UploadToAi
from cookie.model.data import Data as CookieData


class BaseDownload(BaseCrawl):
    def __init__(self, url, start_time, end_time, account, channel, upload=True):
        super(BaseDownload, self).__init__()
        self.__url = url
        self.__start_time = start_time
        self.__end_time = end_time
        self.__account = account
        self.__channel = channel
        self.__upload = upload

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData().get(CookieData.CONST_PLATFORM_TAOBAO_TBK, self.__account)) \
            .set_get_params_kv('startTime', self.__start_time) \
            .set_get_params_kv('endTime', self.__end_time) \
            .set_task_id(md5string(self.__url + self.__start_time + self.__end_time + self.__account + self.__channel))

    def parse_response(self, response, task):
        if 'Content-Type' not in response.headers or 'excel' not in response.headers['Content-Type']:
            processor_logger.error('cookie error')
            assert False, 'cookie 过期'
        file_path = oss.get_key(
            oss.CONST_TALENT_PATH,
            '{account}/{channel}/{start_time}--{end_time}.xls'.format(
                account=self.__account,
                channel=self.__channel,
                start_time=self.__start_time,
                end_time=self.__end_time
            )
        )
        oss.upload_data(file_path, response.content)
        # 爬虫的上传excel有问题，先不分发upload
        if self.__upload:
            self.crawl_handler_page(UploadToAi(file_path))
        return {
            'url': response.url,
            'excelSize': len(response.content),
            'file_path': file_path
        }
