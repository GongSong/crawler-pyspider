import abc
import json
from mq_http_sdk.mq_consumer import Message
from pyspider.helper.date import Date
from pyspider.helper.logging import mq_logger


class Base:
    def __init__(self, msg: Message):
        self._msg = msg
        body = json.loads(msg.message_body)
        body.setdefault('messageId', msg.message_id)
        mq_logger.info('consume message', extra=body)
        self._data = body.get('data')
        self._data_id = body.get('dataId')
        self._publish_time = body.get('publishTime')
        self._publish_service = body.get('publishService')
        self._message_tag = body.get('messageTag')
        self._action = body.get('action')

    @abc.abstractmethod
    def execute(self):
        pass

    def print_basic_info(self):
        """
        打印接受到的基本数据
        :return:
        """
        print("messageId:", self._msg.message_id)
        print("dataId:", self._data_id)
        print("publishTime:", self._publish_time, Date(self._publish_time).format())
        print("publishService:", self._publish_service)
        print("action:", self._action)
        print("now:", Date.now().format())
        print("data:", self._data)
