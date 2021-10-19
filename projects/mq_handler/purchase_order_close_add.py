from mq_handler.base import Base
from mq_handler.sync_mq_handler.purchase_order_close_sync import PurOrderSyncClose
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.date import Date


class PurOrderCloseAdd(Base):
    """
    整单关闭采购跟单并重新创建新采购单
    业务场景：(天鸽系统需要更改采购单里的商品数据，具体的操作为：先关闭老的天鸽采购单，确认关闭成功之后，再添加新的采购单)
    """
    ClOSE_FAIL_TIMES_KEY = 'hupun_purchase_close_fails'  # redis中关闭订单失败次数的key
    # 采购订单不能关闭的状态值
    PUR_COMPLETE = 3  # 已完成
    PUR_CLOSED = 4  # 已关闭
    # 采购跟单的状态值
    NOT_ARRIVED = 0  # 未到货
    PARTIAL_ARRIVED = 1  # 部分到货
    FULL_ARRIVED = 2  # 全部到货, 不能操作关闭
    CLOSED = 3  # 已关闭, 不能操作关闭
    # 关闭备注
    close_remark = 'spider-close-mark'
    # 是否完整关闭了所有的采购单, 默认为True：已完成关闭了所有的采购单
    whole_close = True

    def execute(self):
        print('整单关闭采购跟单并重新创建新采购单')
        self.print_basic_info()

        # 关闭采购单
        close_purchase_obj = self._data.get('closePurchase')
        if close_purchase_obj and isinstance(close_purchase_obj, list):
            print("开始整单关闭采购单")
            # 计数
            count_index = 0
            for item in close_purchase_obj:
                close_success = PurOrderSyncClose(item).execute()
                if not close_success:
                    print("整单关闭采购单失败, data 为：{}".format(item))
                    self.whole_close = False
                    break
                count_index += 1
            # 如果整单关闭的采购单有失败的，待关闭列表还有需要关闭的采购单的话，把之后的采购单全部发送失败的报警
            if count_index < len(close_purchase_obj):
                alarm_list = close_purchase_obj[count_index + 1:]
                for item in alarm_list:
                    from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_CLOSE_RE
                    data_id = item.get('dataId', 0)
                    data = {
                        "code": 1,  # 0：成功 1：失败
                        "errMsg": "前一个采购单整单关闭失败，之后所有需要关闭的采购单直接失败",  # 如果code为1，请将失败的具体原因返回
                    }
                    self.send_mq_msg(data_id, CONST_MESSAGE_TAG_PURCHARSE_CLOSE_RE, data)

        # 新增采购单
        add_purchase_obj = self._data.get('addPurchase')
        if self.whole_close and add_purchase_obj and isinstance(add_purchase_obj, list):
            print("开始新增采购单")
            for item in add_purchase_obj:
                data_id = item.get('dataId', 0)
                email = item.get('email', '')
                add_list = item.get('list', [])
                print("新增采购单, dataId:{}".format(item.get("dataId")))

                # 清除新增采购单的去重缓存
                storage_code = add_list[0].get('storageCode', '')
                tg_purchase_no = add_list[0].get('purchaseNo', '')
                is_second = item.get("isSecond", False)
                self.clear_add_purchase_cache(tg_purchase_no, storage_code, is_second)

                data = {
                    'email': email,
                    'list': add_list
                }
                from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_ADD
                self.send_mq_msg(data_id, CONST_MESSAGE_TAG_PURCHARSE_ADD, data)

    def send_mq_msg(self, data_id, msg_tag, data):
        """
        发送mq消息
        :param data_id:
        :param msg_tag:
        :param data:
        """
        from mq_handler import CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        MQ().publish_message(msg_tag, data, data_id, Date.now().timestamp(), CONST_ACTION_UPDATE)

    @staticmethod
    def clear_add_purchase_cache(tg_purchase_no, storage_code, is_second):
        """
        清除新增采购单的去重缓存
        :param tg_purchase_no: 天鸽采购单
        :param storage_code: 仓库ID
        :param is_second: 是否是采购单70%、30%分批同步的第二批同步
        :return:
        """
        default_storage_redis.delete("{}:{}:{}".format(tg_purchase_no, storage_code, is_second))
