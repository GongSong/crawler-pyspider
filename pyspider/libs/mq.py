from mq_http_sdk.mq_producer import *
from mq_http_sdk.mq_client import *
from pyspider.config import config
from mq_handler.base import Base
from mq_handler import message_tag_to_handler
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.date import Date
from pyspider.helper.logging import mq_logger


class MQ:
    # MQ默认配置项
    CONST_DEFAULT_CONFIG_SECTION = 'rocketmq'
    """
    消息中间件的封装
    """
    def __init__(self, section=''):
        section = section if section else self.CONST_DEFAULT_CONFIG_SECTION
        self.__mq_client = MQClient(
            config.get(section, 'endpoint'),
            config.get(section, 'access_key_id'),
            config.get(section, 'access_key_secret'),
        )
        self.__topic_name = config.get(section, 'topic_name')
        self.__instance_id = config.get(section, 'instance_id')
        self.__group_id = config.get(section, 'group_id')
        self.__publish_service = config.get(section, 'publish_service')
        self.__tracking_file = config.get(section, 'tracking_file')

    def publish_message(self, message_tag, data, data_id='', publish_time=None, action=''):
        """
        发布消息
        :param message_tag:
        :param data:
        :param data_id:
        :param publish_time:
        :param action:
        :return:
        """
        body = {
            'publishService': self.__publish_service,
            'messageTag': message_tag,
            'publishTime': publish_time if publish_time else Date.now().timestamp(),
            'data': data,
            'dataId': data_id,
            'action': action,
        }
        mq_logger.info('publish message', extra=body)
        start_time = time.time() * 1000
        result = self.__mq_client \
            .get_producer(self.__instance_id, self.__topic_name) \
            .publish_message(TopicMessage(json.dumps(body), message_tag))
        body['messageId'] = result.message_id
        body.setdefault('duration', time.time() * 1000 - start_time)
        self.__tracking_publish(body)
        return body

    def consume_message(self, message_tag='', handler=None, batch=3, wait_seconds=5, max_exe_time=300):
        """
        消费消息
        :param message_tag:
        :param handler:
        :param batch:
        :param wait_seconds:
        :param max_exe_time:
        :return:
        """
        from hupun_inventory_onsale.change_double_switch import ChangeDoubleSwitch
        from hupun_inventory_onsale.clear_inventory_ratio import ClearInventoryRatio
        from hupun_inventory_onsale.sync_inventory_ratio import SyncInventoryRatio
        from hupun_inventory_onsale.set_sku_inventory_ratio import SetSkuSearchRatio
        from hupun_inventory_onsale.change_sku_double_switch import ChangeSkuDoubleSwitch
        from hupun_inventory_onsale.clear_sku_inventory_ratio import ClearSkuSearchRatio
        from mq_handler import CONST_MESSAGE_TAG_SYNC_INVENTORY_RATIO, CONST_MESSAGE_TAG_DOUBLE_SWITCH,\
            CONST_MESSAGE_TAG_CLEAR_INVENTORY_RATIO, \
            CONST_MESSAGE_TAG_SYNC_SKU_INVENTORY_RATIO,CONST_MESSAGE_TAG_CLEAR_SKU_INVENTORY_RATIO, \
            CONST_MESSAGE_TAG_SKU_DOUBLE_SWITCH

        message_tag_to_handler_update = {
            CONST_MESSAGE_TAG_DOUBLE_SWITCH: ChangeDoubleSwitch,
            CONST_MESSAGE_TAG_SYNC_INVENTORY_RATIO: SyncInventoryRatio,
            CONST_MESSAGE_TAG_CLEAR_INVENTORY_RATIO: ClearInventoryRatio,
            CONST_MESSAGE_TAG_SYNC_SKU_INVENTORY_RATIO: SetSkuSearchRatio,
            CONST_MESSAGE_TAG_CLEAR_SKU_INVENTORY_RATIO: ClearSkuSearchRatio,
            CONST_MESSAGE_TAG_SKU_DOUBLE_SWITCH: ChangeSkuDoubleSwitch,
        }
        message_tag_to_handler.update(message_tag_to_handler_update)
        consumer = self.__mq_client.get_consumer(self.__instance_id, self.__topic_name, self.__group_id, message_tag)
        end_time = Date.now().plus_seconds(max_exe_time).timestamp()
        # 每五分钟重启消费进程, 保证代码是最新的
        while Date.now().timestamp() < end_time:
            try:
                resp_msgs = consumer.consume_message(batch, wait_seconds)
            except MQExceptionBase as e:
                if e.type == "MessageNotExist":
                    print("No new message! RequestId: %s" % e.req_id)
                    continue
                print("Consume Message Fail! Exception: %s\n" % e)
                continue
            for msg in resp_msgs:
                body = json.loads(msg.message_body)
                body.setdefault('messageId', msg.message_id)
                body.setdefault('nextConsumeTime', msg.next_consume_time)
                start_time = time.time() * 1000
                body.setdefault('consumeTimeM', start_time)
                body.setdefault('publishTimeM', msg.publish_time)
                body.setdefault('delay', body['consumeTimeM'] - body['publishTimeM'])
                try:
                    # 消息重复了(消息中间件有一定的小概率会重复消费)
                    if not default_storage_redis.lock('mqc_'+msg.message_id, 3600):
                        body.setdefault('consumeResult', None)
                        body.setdefault('consumeStatus', 'repeat')
                    elif handler and issubclass(handler, Base):
                        body.setdefault('consumeResult', handler(msg).execute())
                        body.setdefault('consumeStatus', 'ok')
                    else:
                        current_handler = message_tag_to_handler.get(msg.message_tag)
                        if current_handler:
                            body.setdefault('consumeResult', current_handler(msg).execute())
                            body.setdefault('consumeStatus', 'ok')
                        else:
                            body.setdefault('consumeStatus', 'break')

                except Exception as e:
                    body.setdefault('consumeResult', str(e))
                    body.setdefault('consumeStatus', 'err')
                body.setdefault('duration', time.time() * 1000 - start_time)
                self.__tracking_consume(body)

            # msg.next_consume_time前若不确认消息消费成功，则消息会重复消费
            # 消息句柄有时间戳，同一条消息每次消费拿到的都不一样
            try:
                receipt_handle_list = [msg.receipt_handle for msg in resp_msgs]
                consumer.ack_message(receipt_handle_list)
                print("Ak %s Message Succeed.\n\n" % len(receipt_handle_list))
            except MQExceptionBase as e:
                print("\nAk Message Fail! Exception: %s" % e)

    def __tracking(self, data):
        if self.__tracking_file:
            data['currentGroupId'] = self.__group_id
            data['time'] = Date().now().format()
        with open(self.__tracking_file, 'a') as f:
            f.write(json.dumps(data)+"\n")

    def __tracking_publish(self, data):
        data['type'] = 'publish'
        self.__tracking(data)

    def __tracking_consume(self, data):
        data['type'] = 'consume'
        self.__tracking(data)
