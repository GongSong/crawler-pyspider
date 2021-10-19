import json

from pyspider.libs.base_crawl import *
from backstage_data_migrate.config import *
from pyspider.helper.date import Date
from backstage_data_migrate.model.backstage_migrate import Backstage
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class RedbookFlowData(BaseCrawl):
    URL = 'https://ark.xiaohongshu.com/api/ark/chaos/trd/seller/channel?last_days={}'
    website = 'redbook'

    def __init__(self, username, day=1):
        super(RedbookFlowData, self).__init__()
        # day 表示近几天
        self.__day = day
        self.__username = username
        self.__url = self.URL.format(day)

    def crawl_builder(self):
        cookies_dict_trans = {}
        cookies_dict = [i.strip().split('=', 1) for i in
                        CookieData.get(CookieData.CONST_PLATFORM_REDBOOK, self.__username).split(';')]
        for cookie in cookies_dict:
            cookies_dict_trans[cookie[0]] = cookie[1]
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies_dict(cookies_dict_trans) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.__username + self.__url)) \
            .schedule_age(1)

    def parse_response(self, response, task):
        yesterday = Date.now().plus_days(-self.__day).format(full=False)
        redbook_name = 'redbook:flow:{}'.format(yesterday)
        content = response.text
        try:
            js_content = json.loads(content)
            data = js_content['data']['channels']
            if data:
                data_type = '小红书流量来源'
                processor_logger.info('获取到了小红书流量来源{}的数据'.format(redbook_name))

                goods = Backstage().find_one({
                    'result.website': self.website,
                    'result.username': redbook_name
                })
                if goods is not None:
                    processor_logger.info('有数据，更新：{}'.format(redbook_name))
                    Backstage().update({
                        'result.website': self.website,
                        'result.username': redbook_name
                    },
                        {
                            'data': json.dumps(data),
                            'data_type': data_type,
                            'create_time': yesterday,
                            'url': self.__url
                        })
                else:
                    return {
                        'website': self.website,
                        'data': json.dumps(data),
                        'data_type': data_type,
                        'create_time': yesterday,
                        'url': self.__url
                    }
            else:
                processor_logger.warning('获取小红书流量来源失败')
        except Exception as e:
            processor_logger.exception('获取小红书流量来源失败{}!'.format(redbook_name, e))
