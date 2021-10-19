from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date

import uuid


class DingTalk(BaseCrawl):
    BASED_URL = ROBOT_URL = 'https://oapi.dingtalk.com/robot/send?access_token={}'

    def __init__(self, token, title, content):
        super(DingTalk, self).__init__()
        self.__uuid = uuid.uuid4()
        self.__url = self.BASED_URL.format(token)
        self.__content = content
        self.__title = title
        self.__date = Date.now().format()

    def crawl_builder(self):
        text = """# {title}
```
{time}
{content}
```     
        """.format(title=self.__title, time=self.__date, content=self.__content)
        data = {"msgtype": "markdown", "markdown": {"title": self.__title, "text": text},
                "at": {"atMobiles": [], "isAtAll": False}}
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_kwargs_kv('validate_cert', False) \
            .set_task_id(md5string(self.__uuid)) \
            .set_post_json_data(data)

    def parse_response(self, response, task):
        return {
            'response': response.json,
            'url': self.__url,
            'title': self.__title,
            'msg': self.__content,
            'timestamp': self.__date,
        }
