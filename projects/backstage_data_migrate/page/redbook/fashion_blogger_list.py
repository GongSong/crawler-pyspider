import json
import uuid

from backstage_data_migrate.model.es.redbook_blogger_data import RedbookBloggerData
from backstage_data_migrate.page.redbook.live_data import LiveData
from cookie.model.data import Data as CookieData
from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from backstage_data_migrate.config import *


class FashionBloggerList(BaseCrawl):
    """
    获取时尚博主列表
    """
    URL = 'https://influencer.xiaohongshu.com/api/solar/cooperator/live/query?' \
          'column=livecomprehensiverank&sort=asc&location=&type=时尚&pageNum={page_num}&pageSize={page_size}&cps=true'

    def __init__(self, user_name, page=1, page_size=20, crawl_next_page=False):
        super(FashionBloggerList, self).__init__()
        self.__url = self.URL.format(page_num=page, page_size=page_size)
        self.user_name = user_name
        self.__page = page
        self.__page_size = page_size
        self.crawl_next_page = crawl_next_page

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
        if resp_json.get('data', {}).get('kols', []):
            for item in resp_json.get('data', {}).get('kols', []):
                user_id = item.get('userId')
                name = item.get('name')
                red_id = item.get('redId')
                fans_count = item.get('fansCount')
                save_dict = {
                    'user_id': user_id,
                    'name': name,
                    'red_id': red_id,
                    'fans_count': fans_count,
                    'blogger_info': item,
                    'sync_time': sync_time,
                }
                save_list.append(save_dict)

                # 抓取博主的直播数据详情
                api_keywords = ['fans_profile', 'fans_overall_history', 'live_overall', 'live_history', 'cps_overall']
                for keyword in api_keywords:
                    self.crawl_handler_page(LiveData(self.user_name, user_id, keyword))

            RedbookBloggerData().update(save_list, async=True)

            # 抓取下一页
            if self.crawl_next_page:
                self.crawl_handler_page(FashionBloggerList(self.user_name, self.__page + 1, self.__page_size, self.crawl_next_page))
        return {
            'sync_time': sync_time,
        }


if __name__ == '__main__':
    FashionBloggerList(1, 20).get_result()
