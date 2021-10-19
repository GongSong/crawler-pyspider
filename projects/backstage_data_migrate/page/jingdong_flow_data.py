import uuid

from backstage_data_migrate.config import *
from pyspider.libs.base_crawl import *
from backstage_data_migrate.redis_utils import save_to_redis
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class JDFlowData(BaseCrawl):
    URL = 'https://sz.jd.com/sz/api/viewflow/exportMyAttentionSourceData.ajax#{}'

    def __init__(self, date_type, device, start_date, end_date, type_date, username):
        super(JDFlowData, self).__init__()
        self.__date_type = date_type
        self.__device = device
        self.__start_date = start_date
        self.__end_date = end_date
        self.__type_date = type_date
        self.__username = username
        self.__channel_name = 'jingdong:{}_req_{}:{}' \
            .format(self.__date_type, self.__device, self.__start_date)
        self.__url = self.URL.format(md5string(
            ':'.join([date_type, device, start_date, end_date, type_date, username]))
        )

    def crawl_builder(self):
        # 获取cookie登录
        processor_logger.info('get cookies')
        cookies = CookieData.get(CookieData.CONST_PLATFORM_JINGDONG, CookieData.CONST_USER_JINGDONG[0][0])
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(cookies) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_post_data(self.get_data_form()) \
            .set_task_id(md5string(self.__device + self.__url)) \
            .schedule_age(1)

    def parse_response(self, response, task):
        # 保存数据到redis
        save_to_redis(self.__channel_name, response)
        # 保存数据到oss
        file_path = oss.get_key(
            oss.CONST_JD_FLOW_PATH,
            '{date_type}/{device}/{start_date}--{end_date}.xls'.format(
                date_type=self.__date_type,
                device=self.__device,
                start_date=self.__start_date,
                end_date=self.__end_date
            )
        )
        oss.upload_data(file_path, response.content)

    def get_data_form(self):
        device_mapping = {
            'app': 2,
            'pc': 20,
            'wechat': 3,
            'mobileq': 4,
            'mport': 1
        }
        return {
            'startDate': self.__start_date,
            'endDate': self.__end_date,
            'date': self.__type_date,
            'indChannel': device_mapping.get(self.__device)
        }
