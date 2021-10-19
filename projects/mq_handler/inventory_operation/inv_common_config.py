import traceback
from copy import deepcopy

from alarm.page.ding_talk import DingTalk
from hupun_operator.page.inventory.inventory_conf_list import InventoryConfList
from hupun_operator.page.inventory.inventory_sync_common import InvSyncCommon
from hupun_operator.page.inventory.inventory_sync_operate import InvSyncOperate
from hupun_slow_crawl.model.es.store_house import StoreHouse
from mq_handler.base import Base
from pyspider.core.model.storage import StorageRedis, default_storage_redis
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.date import Date


class InvCommonConfig(Base):
    """
    库存通用配置的更改
    """
    ROBOT_TOKEN = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
    # 保存状态的redis的配置，
    # 线上环境
    REDIS_HOST = '10.0.5.5'
    REDIS_PORT = 5304
    REDIS_DB = 0
    # 测试环境
    # REDIS_HOST = '10.0.5.5'
    # REDIS_PORT = 5303
    # REDIS_DB = 8
    # key 对应的值: 2，操作中；1，操作完成；0，操作失败
    REDIS_KEY = 'shelf.syncCommonInv'

    # 重置状态，用于库存配置更改后的商品从头开始上传
    goods_upload_status = 'goodsUploadStatus'

    def execute(self):
        print('库存通用配置的更改')
        self.print_basic_info()
        # 写入数据
        self.handle_data()

    def handle_data(self):
        """
        数据处理区
        :return:
        """
        try:
            print('开始数据处理')
            if not isinstance(self._data.get('data'), list):
                assert False, '传入的更改库存通用配置的数据结构不对，不是list'
            self.change_inv_config()

            # !!!!!!!!暂时停止以下自动同步上传库存的代码!!!!!!!!
            print('暂时停止自动同步上传库存的代码')
            # print('更改完库存通用配置之后，停止之前的库存商品上传')
            # status_timestamp = Date.now().timestamp()
            # default_storage_redis.set(self.goods_upload_status, status_timestamp)

            # print('更改完库存通用配置之后，上传更新所有的库存商品')
            # InvSyncCommon().sync_inventory_goods(is_all=True, status_value=status_timestamp)
        except Exception as e:
            err_msg = "库存通用配置同步出现错误:{}".format(e)
            print('err_msg', err_msg)
            print(traceback.format_exc())
            # 添加报警通知
            if CrawlerHelper.in_project_env():
                title = '库存通用配置同步发生未知异常'
                ding_msg = err_msg
                DingTalk(self.ROBOT_TOKEN, title, ding_msg).enqueue()

    def change_inv_config(self):
        """
        更改库存通用配置
        :return:
        """
        try:
            print('开始更改库存通用配置')

            # 设置库存通用配置的redis的状态
            StorageRedis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB).set(self.REDIS_KEY, 2)

            received_data = self._data.get('data')
            # 去重
            received_data = [dict(t) for t in set([tuple(d.items()) for d in received_data])]
            # 把 storage_uid 转换为 storage_name
            for _data in received_data:
                storage_uid = _data['storage_uid']
                storage_name = StoreHouse().get_name_by_uid(storage_uid)
                if not storage_name:
                    err_msg = '仓库uid:{}找不到，请检查重新输入'.format(storage_uid)
                    raise Exception(err_msg)
                _data['storage_name'] = storage_name

            # 获取库存同步的列表
            inv_list_obj = InventoryConfList().use_cookie_pool()
            inv_status, inv_list_result = CrawlerHelper.get_sync_result(inv_list_obj)
            if inv_status == 1:
                assert False, '爬虫获取库存同步list失败:{}'.format(inv_list_result)
            self.sync_inventory_conf_args(inv_list_result['response'], received_data)

            # 保存库存同步的状态: 2，操作中；1，操作完成；0，操作失败
            # 操作完成
            StorageRedis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB).set(self.REDIS_KEY, 1)
        except Exception as e:
            err_msg = "更改库存通用配置出现错误:{}".format(e)
            print('err_msg', err_msg)
            print(traceback.format_exc())
            # 操作失败
            StorageRedis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB).set(self.REDIS_KEY, 0)
            # 发送库存配置更改失败的报警通知
            if CrawlerHelper.in_project_env():
                title = '更改库存通用配置出现错误'
                ding_msg = err_msg
                DingTalk(self.ROBOT_TOKEN, title, ding_msg).enqueue()

    def sync_inventory_conf_args(self, inv_list, received_data):
        """
        获取库存通用配置更改的请求参数结构体
        :param inv_list: 库存手动（自动）同步详情的所有数据
        :param received_data: 接收到的库存配置信息
        :return:
        """
        print('开始获取库存通用配置更改的请求参数结构体')
        inv_list = deepcopy(inv_list)
        quantity_types = {
            '实际库存': '0',
            '可用库存': '1',
            '在途库存': '4',
            '实际库存+在途库存': '2',
            '可用库存+在途库存': '3',
        }
        # 把库存从中文转换成数字
        for _data in received_data:
            if quantity_types.get(_data['quantity_type']):
                _data['quantity_type'] = int(quantity_types.get(_data['quantity_type']))
            else:
                assert False, '查询不到库存:{}的编号数据'.format(_data['quantity_type'])
        # 选出需要关闭和开启的库存同步配置项
        print('选出需要关闭和开启的库存同步配置项')
        open_sync_config = []
        close_sync_config = []
        for _re in received_data:
            for index, _inv in enumerate(inv_list):
                outer_wrapper_data = deepcopy(_inv)
                if _re['shop_name'] == _inv['shop_name'] and _re['storage_name'] == _inv['storage_name']:
                    outer_wrapper_data['openAuto'] = _re['open_auto']
                    outer_wrapper_data['upload_ratio'] = _re['upload_ratio']
                    outer_wrapper_data['upload_beyond'] = _re['upload_beyond']
                    outer_wrapper_data['quantity_type'] = _re['quantity_type']
                    open_sync_config.append(outer_wrapper_data)
                    break
                elif index == len(inv_list) - 1:
                    assert False, '找不到店铺:{}对应的万里牛库存配置数据'.format(_re['shop_name'])
        for _inv in inv_list:
            if not _inv['openAuto']:
                continue
            for index, _conf in enumerate(open_sync_config):
                if _conf['shop_name'] == _inv['shop_name'] and _conf['storage_name'] == _inv['storage_name']:
                    break
                elif index == len(open_sync_config) - 1:
                    close_sync_config.append(_inv)

        # 构造需要更改的配置数据
        print('构造需要更改的配置数据')
        sync_data = []
        for _open in open_sync_config:
            old_data = deepcopy(_open)
            old_data['$oldData'] = {}
            for inv in inv_list:
                if inv['shop_name'] == _open['shop_name'] and inv['storage_name'] == _open['storage_name']:
                    old_data['$oldData'] = inv
            old_data['$dataType'] = 'v:inventory.sync$SynPolicy'
            old_data['$state'] = '2'
            old_data['$entityId'] = '0'
            sync_data.append(old_data)
        for _close in close_sync_config:
            old_data = deepcopy(_close)
            old_data['$oldData'] = {}
            for inv in inv_list:
                if inv['shop_name'] == _close['shop_name'] and inv['storage_name'] == _close['storage_name']:
                    old_data['$oldData'] = inv
            old_data['upload_ratio'] = None
            old_data['upload_beyond'] = None
            old_data['openAuto'] = False
            old_data['$dataType'] = 'v:inventory.sync$SynPolicy'
            old_data['$state'] = '2'
            old_data['$entityId'] = '0'
            sync_data.append(old_data)

        # 发送更新配置的请求
        print('发送更新配置的请求')
        ope_obj = InvSyncOperate(sync_data).use_cookie_pool()
        ope_status, ope_result = CrawlerHelper.get_sync_result(ope_obj)
        if ope_status == 1:
            assert False, '操作更改库存同步配置失败:{}'.format(ope_result)
        if not ope_result.get('response', {}).get('entityStates', {}):
            assert False, '操作更改库存同步配置失败,获取到的响应不对:{}'.format(ope_result)
        print('更改本次库存同步的配置成功')
