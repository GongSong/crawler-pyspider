import fire
from pyspider.helper.date import Date
from pyspider.libs.mq import MQ
from mq_handler import CONST_MESSAGE_TAG_PRINT


class Cron:
    def publish_message(self):
        MQ().publish_message(CONST_MESSAGE_TAG_PRINT, 'data', 'pyspider', Date.now().timestamp(), 'update')

    def consume_message(self, message_tag='', batch=3, wait_seconds=5, max_exe_time=300):
        MQ().consume_message(message_tag=message_tag, batch=batch, wait_seconds=wait_seconds, max_exe_time=max_exe_time)


if __name__ == '__main__':
    fire.Fire(Cron)
