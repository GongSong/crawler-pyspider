# coding=utf-8

from .mq_request import ConsumeMessageRequest, ConsumeMessageResponse, AckMessageRequest, AckMessageResponse

try:
    import json
except ImportError as e:
    import simplejson as json


class MQConsumer:
    def __init__(self, instance_id, topic_name, consumer, message_tag, mq_client, debug=False):
        if instance_id is None:
            self.instance_id = ""
        else:
            self.instance_id = instance_id
        self.topic_name = topic_name
        self.consumer = consumer
        self.message_tag = message_tag
        self.mq_client = mq_client
        self.debug = debug

    def set_debug(self, debug):
        self.debug = debug

    def consume_message(self, batch_size=1, wait_seconds=-1):
        """ 消费消息

            @type batch_size: int
            @param batch_size: 本次请求最多获取的消息条数，1~16

            @type wait_seconds: int
            @param wait_seconds: 本次请求的长轮询时间，单位：秒，1～30

            @rtype: list of Message object
            @return 多条消息的属性，包含消息的基本属性、下次可消费时间和临时句柄

            @note: Exception
            :: MQClientParameterException  参数格式异常
            :: MQClientNetworkException    网络异常
            :: MQServerException           处理异常
        """
        req = ConsumeMessageRequest(self.instance_id, self.topic_name, self.consumer, batch_size, self.message_tag, wait_seconds)
        resp = ConsumeMessageResponse()
        self.mq_client.consume_message(req, resp)
        self.debuginfo(resp)
        return self.__batchrecv_resp2msg__(resp)

    def ack_message(self, receipt_handle_list):
        """确认消息消费成功，如果未在300秒内确认则认为消息消费失败，通过consume_message能再次收到改消息

            @type receipt_handle_list: list, size: 1~16
            @param receipt_handle_list: consume_message返回的多条消息的临时句柄

            @note: Exception
            :: MQClientParameterException  参数格式异常
            :: MQClientNetworkException    网络异常
            :: MQServerException           处理异常
        """
        req = AckMessageRequest(self.instance_id, self.topic_name, self.consumer, receipt_handle_list)
        resp = AckMessageResponse()
        self.mq_client.ack_message(req, resp)
        self.debuginfo(resp)

    def debuginfo(self, resp):
        if self.debug:
            print("===================DEBUG INFO===================")
            print("RequestId: %s" % resp.header["x-mq-request-id"])
            print("================================================")

    def __batchrecv_resp2msg__(self, resp):
        msg_list = []
        for entry in resp.message_list:
            msg = Message()
            msg.message_id = entry.message_id
            msg.message_body_md5 = entry.message_body_md5
            msg.consumed_times = entry.consumed_times
            msg.publish_time = entry.publish_time
            msg.first_consume_time = entry.first_consume_time
            msg.message_body = entry.message_body
            msg.next_consume_time = entry.next_consume_time
            msg.receipt_handle = entry.receipt_handle
            msg.message_tag = entry.message_tag
            msg_list.append(msg)
        return msg_list


class Message:
    def __init__(self):
        """ 消息属性
            :: message_body         消息体
            :: message_id           消息编号
            :: message_body_md5     消息体的MD5值
            :: consumed_times       消息被消费的次数
            :: publish_time         消息发送的时间，单位：毫秒
            :: first_consume_time   消息第一次被消费的时间，单位：毫秒
            :: receipt_handle       下次删除的临时句柄，next_consume_time之前有效
            :: next_consume_time    消息下次可消费时间
        """
        self.message_body = ""
        self.message_tag = None

        self.message_id = ""
        self.message_body_md5 = ""

        self.consumed_times = -1
        self.publish_time = -1
        self.first_consume_time = -1

        self.receipt_handle = ""
        self.next_consume_time = 1
