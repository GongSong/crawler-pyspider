import json
import random
import uuid

from pyspider.libs.base_crawl import *


class Bulk(BaseCrawl):
    def __init__(self, nodes: list, es_index: str, es_type: str, body: list):
        super(Bulk, self).__init__()
        self.__nodes = nodes
        self.__es_index = es_index
        self.__es_type = es_type
        self.__body = body
        self.__task_id = uuid.uuid4()

    def crawl_builder(self):
        body = self.__body
        if not isinstance(body, (str, bytes)):
            body = '\n'.join(map(json.dumps, body))
            body += '\n'
        return CrawlBuilder() \
            .set_url('{}/_bulk'.format(random.choice(self.__nodes).rstrip('/'))) \
            .set_headers_kv('content-type', 'application/x-ndjson') \
            .set_task_id(self.__task_id) \
            .schedule_retries(1) \
            .set_post_data(body)

    def parse_response(self, response, task):
        return {
            'result': response.json,
            'es_index': self.__es_index,
            'es_type': self.__es_type,
            'count': len(self.__body)/2
        }
