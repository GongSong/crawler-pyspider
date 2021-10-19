import traceback
from copy import deepcopy

from alarm.page.ding_talk import DingTalk
from hupun_operator.page.warehouse.extra_store_query import ExtraStoreQuery
from hupun_operator.page.warehouse.extra_store_setting import ExtraStoreSetting
from hupun_slow_crawl.model.es.store_house import StoreHouse
from mq_handler.base import Base
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.date import Date
from pyspider.helper.input_data import InputData


class WarehouseStoreSet(Base):
    """
    万里牛包含【预售SKU】的订单拆单
    """
    # 店铺名和对应的仓库uid
    storage_uid_shop = []
    # 报警的钉钉机器人
    ROBOT_TOKEN = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'

    def execute(self):
        print('更改【仓库匹配】的例外店铺设置中的店铺和仓库对应关系')
        self.print_basic_info()

        # 写入数据
        try:
            if not isinstance(self._data.get('data'), list):
                raise Exception('传入的数据格式不对')

            # 查询例外店铺设置的数据
            store_query = ExtraStoreQuery().set_cookie_position(1)
            store_query_st, store_query_re = CrawlerHelper.get_sync_result(store_query)
            if store_query_st == 1 or not store_query_re or not isinstance(store_query_re, list):
                raise Exception('未查询到例外店铺设置的数据,error:{}'.format(store_query_re))

            # 开始设置例外店铺的对应关系
            for data in self._data.get('data'):
                shop_name = InputData(data).get_str('channel')
                storage_code = InputData(data).get_str('storage_code')
                if not shop_name or not storage_code:
                    raise Exception('传入的shop_name或者storage_code不符合要求')

                print('开始操作店铺:{}的仓库:{}设置'.format(shop_name, storage_code))
                self.set_store_config(shop_name, storage_code, store_query_re)
                print('完成操作店铺:{}的仓库:{}设置'.format(shop_name, storage_code))

            # 更改库存配置
            # 更新：应业务方要求,取消更改库存配置
            # self.change_inventory_setting()
            print('发送更改库存配置完成')

        except Exception as e:
            err_msg = '更改【仓库匹配】的例外店铺设置中的店铺和仓库对应关系error:{};'.format(e)
            print(err_msg)
            print(traceback.format_exc())

            # 发送钉钉报警
            print('发送钉钉报警')
            title = '更改【仓库匹配】的例外店铺设置中的店铺和仓库对应关系异常'
            text = err_msg
            DingTalk(self.ROBOT_TOKEN, title, text).enqueue()

    def set_store_config(self, shop_name, storage_code, store_query_re):
        """
        执行添加例外店铺设置的操作
        :param shop_name:
        :param storage_code:
        :param store_query_re:
        :return:
        """
        print('开始执行添加例外店铺设置的操作')

        # 输入信息
        input_shop_name = shop_name
        store_query_re = deepcopy(store_query_re)

        # 判断传入的店铺是否已经绑定好仓库了
        aim_shop_data = {}
        for index, re in enumerate(store_query_re):
            shop_whole_name = re['shopName']
            if input_shop_name not in shop_whole_name and index == len(store_query_re) - 1:
                raise Exception('查不到传入的店铺:{}'.format(input_shop_name))
            if input_shop_name in shop_whole_name:
                aim_shop_data = deepcopy(re)
                break
        shop_uid = aim_shop_data['shopUid']
        shop_whole_name = aim_shop_data['shopName']

        print('shop_uid', shop_uid)
        print('shop_whole_name', shop_whole_name)
        storage_uid, storage_name = StoreHouse().get_uid_and_name_by_code(storage_code)
        if not storage_uid or not storage_name:
            raise Exception('没有查询到storage_code:{}对应的storage_name或者storage_uid'.format(storage_code))
        print('storage_uid', storage_uid)
        print('storage_name', storage_name)

        # 添加更改例外店铺设置
        re = ExtraStoreSetting(shop_uid, shop_whole_name, storage_uid, storage_name) \
            .set_cookie_position(1) \
            .get_result()

        # 删除更改例外店铺设置
        # re = ExtraStoreDelete(shop_uid, shop_whole_name, storage_name) \
        #     .set_cookie_position(1) \
        #     .get_result()

        print('更改例外店铺设置之后的返回结果:{}'.format(re))
        if isinstance(re, dict):
            print('设置例外店铺:{}成功'.format(input_shop_name))
            # 设置库存配置的仓库uid
            self.storage_uid_shop.append({
                'shop_name': shop_name,
                'storage_uid': storage_uid,
            })
        else:
            err_msg = '设置例外店铺:{}失败, 返回的结果:{}'.format(input_shop_name, re)
            raise Exception(err_msg)

    def change_inventory_setting(self):
        """
        更改库存配置
        :return:
        """
        # 库存同步的通用配置更改
        # 组合店铺对应的仓库uid
        data = {'data': [
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",  # 默认为总仓, 如果有其他仓就改为其他仓
                "shop_name": "icy旗舰店",  # 天猫旗舰店
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "穿衣助手旗舰店",  # 京东
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "iCY设计师集合店",  # APP
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "ICY小红书",  # 小红书
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "ICY奥莱",  # 奥莱店
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "ICY唯品会",  # 唯品会
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "ICY设计师平台",  # 淘宝
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            }
        ]}
        for inner_data in data['data']:
            for s_index, storage_item in enumerate(self.storage_uid_shop):
                if storage_item['shop_name'] == inner_data['shop_name']:
                    inner_data['storage_uid'] = storage_item['storage_uid']
                    break
                elif s_index == len(self.storage_uid_shop) - 1:
                    raise Exception('店铺:{}找不到对应的仓库uid'.format(inner_data['shop_name']))

        data_id = '2340349'
        from pyspider.libs.mq import MQ
        from mq_handler import CONST_MESSAGE_TAG_SYNC_COMMON_INV, CONST_ACTION_UPDATE
        MQ().publish_message(CONST_MESSAGE_TAG_SYNC_COMMON_INV, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)
