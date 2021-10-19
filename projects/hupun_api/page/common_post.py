import uuid
from hupun_api.page.base import *


class CommonPost(Base):
    """
    通用的post请求
    """

    def __init__(self, path):
        super(CommonPost, self).__init__(path)

    def parse_response(self, response, task):
        return response.json

    def get_unique_define(self):
        return uuid.uuid4()
