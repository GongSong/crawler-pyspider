import json
import uuid

from backstage_data_migrate.model.es.redbook_blogger_data import RedbookBloggerData
from cookie.model.data import Data as CookieData
from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from backstage_data_migrate.config import *


class LiveData(BaseCrawl):
    """
    获取时尚博主的 直播数据，带货数据，粉丝分析
    """
    URL = 'https://influencer.xiaohongshu.com/api/solar/kol/data/{user_id}/{keyword}'

    def __init__(self, user_name, user_id, keyword):
        super(LiveData, self).__init__()
        self.user_name = user_name
        self.user_id = user_id
        self.keyword = keyword
        self.__url = self.URL.format(user_id=user_id, keyword=keyword)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_REDBOOK, self.user_name)) \
            .set_task_id(md5string(self.__url + str(uuid.uuid4())))

    def parse_response(self, response, task):
        sync_time = Date.now().format()
        save_list = []
        resp_json = json.loads(response.text)
        if resp_json.get('data', {}):
            save_dict = {
                'user_id': self.user_id,
                self.keyword: resp_json.get('data', {}),
                'sync_time': sync_time,
            }
            save_list.append(save_dict)

        RedbookBloggerData().update(save_list, async=True)
        return {
            'sync_time': sync_time,
        }
