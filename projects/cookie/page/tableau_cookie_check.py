import uuid

from cookie.config import *
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData


class TableauCoCheck(BaseCrawl):
    """
    tableau 检测 cookie 是否失效的模块
    """

    URL = 'https://tableau.ichuanyi.com/vizportal/api/web/v1/getViews'
    PAYLOAD = {
        "method": "getViews",
        "params": {
            "order": [
                {
                    "field": "hitsLastOneMonthTotal",
                    "ascending": False
                }
            ],
            "page": {
                "startIndex": 0,
                "maxItems": 100
            },
            "statFields": [
                "hitsTotal",
                "hitsLastOneMonthTotal",
                "hitsLastThreeMonthsTotal",
                "hitsLastTwelveMonthsTotal",
                "favoritesTotal"
            ]
        }
    }

    def __init__(self, username):
        super(TableauCoCheck, self).__init__()
        self.__username = username

    def crawl_builder(self):
        cookies = CookieData.get(CookieData.CONST_PLATFORM_TABLEAU, self.__username)
        xsrf_token = ''
        if cookies:
            xsrf_token = cookies.split('XSRF-TOKEN=')[1].split(';')[0]
        builder = CrawlBuilder() \
            .set_url(self.URL + "#{}".format(uuid.uuid4())) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TABLEAU, self.__username)) \
            .update_kwargs_kv('headers', {'X-XSRF-TOKEN': xsrf_token}) \
            .set_post_json_data(self.PAYLOAD)
        return builder

    def parse_response(self, response, task):
        return response.text
