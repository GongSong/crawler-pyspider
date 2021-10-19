import random
import traceback
from copy import deepcopy

import time

from hupun_operator.model.es.inventory_sync import InventorySync
from hupun_operator.page.inventory.inventory_conf_list import InventoryConfList
from hupun_operator.page.inventory.inventory_upload import InvUpload
from hupun_slow_crawl.model.es.inventory_sync_goods_es import InvSyncGoodsEs
from hupun_slow_crawl.model.es.inventory_sync_goods_sku_es import InvSyncGoodsSkuEs
from pyspider.core.model.storage import default_storage_redis, ai_storage_redis
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.date import Date
from pyspider.helper.utils import generator_list


class InvSyncCommon:
    """
    上传库存的通用操作
    """
    # 进度程度的redis key
    FLAG = 'spu'
    PROGRESS_RUNNING = 'inv_sync'
    STEP = 20

    def __init__(self):
        self.__sync_config = None
        self.__inv_goods_upload = 'goodsUploadStatus'
        self.__combined_key = ''

    def set_sync_flag(self, flag='spu'):
        """
        设置上传库存的类型，默认为上传spu
        :param flag: 目前有spu和sku
        :return:
        """
        self.FLAG = flag
        return self

    def sync_inventory_goods(self, spus='', is_all=False, status_value=0):
        """
        手动或者全量同步库存商品
        :param spus: 需要同步的spu
        :param is_all: 是否全量同步商品
        :param status_value: 用来判断当前的全量同步操作是否要停止,有新的全量同步操作应该要把老的同步请求关闭
        :return:
        """
        sync_time = Date.now().format_es_utc_with_tz()
        if is_all:
            print('同步全量库存商品')
            # 全量更新时，flag默认为spu
            self.FLAG = 'spu'
            # 全量更新
            goods = InvSyncGoodsEs().get_all_inv_goods()
            for g in goods:
                # 判断是否有新的同步操作过来，有则停止库存商品上传
                if int(default_storage_redis.get(self.__inv_goods_upload)) != status_value:
                    print('有新的全量同步操作,把老的同步请求关闭')
                    return
                goods_copy = deepcopy(g)
                self.__combined_key = self.PROGRESS_RUNNING + ':' + self.FLAG
                self.upload_inv_sync(goods_list=goods_copy)
            print('同步全量库存商品完成')
        else:
            print('手动同步部分库存商品')
            # 部分更新
            if not isinstance(spus, list):
                assert False, '手动同步库存商品传入的spu不是list'
            if self.FLAG == 'sku':
                spus, spu_and_sku = self.get_combine_spu_sku(spus)
            self.__combined_key = self.PROGRESS_RUNNING + ':' + self.FLAG
            for spu_list in generator_list(spus, 20):
                # 可用的商品信息
                goods_list = []
                # 错误商品的信息
                return_list = []
                for spu in spu_list:
                    spu_data = InvSyncGoodsEs().get_single_inv_goods(spu)
                    if not spu_data:
                        err_msg = '商品:{}在万里牛查不到'.format(spu)
                        print('err_msg', err_msg)
                        return_msg = {
                            'spuBarcode': spu,
                            'syncTime': sync_time,
                            'failReason': err_msg,
                            'syncStatus': '1',
                            'flag': self.FLAG,
                        }
                        return_list.append(return_msg)
                    else:
                        goods_list.append(spu_data)
                InventorySync().update(return_list, async=True)
                if not goods_list:
                    print('没有查询到需要上传的商品列表')
                    continue
                # 执行上传库存操作
                if self.FLAG == 'spu':
                    # 根据spu上传库存
                    self.upload_inv_sync(goods_list=goods_list)
                else:
                    # 根据sku上传库存
                    self.upload_inv_sync(goods_list=goods_list, spu_sku_relation=spu_and_sku)
            print('手动同步部分库存商品完成')
        # 已经上传完了，清空进度redis
        print('已经上传完了，清空进度redis')
        ai_storage_redis.set(self.__combined_key, 0)

    def upload_inv_sync(self, goods_list=None, spu_sku_relation=None):
        """
        上传库存商品
        :param goods_list: 需要上传的库存商品
        :param spu_sku_relation: 如果是同步sku，那么spu_sku_relation用来提供spu和sku的对应关系
        :return:
        """
        # 对应spu同步
        if spu_sku_relation is None:
            spu_sku_relation = {}
        if goods_list is None:
            goods_list = []
        barcode_list = []
        # 对应sku同步
        sku_list = []
        try:
            print('开始操作上传spu库存商品')
            # 同步配置
            if not self.__sync_config:
                self.__sync_config = self.get_upload_inv_config()
            sync_config = self.get_upload_inv_config()
            sync_goods = []
            for _g in goods_list:
                barcode_list.append(_g['spec_code'])
                outer_goods = deepcopy(_g)
                outer_goods['$dataType'] = 'v:inventory.sync$Inventory'
                outer_goods['$entityId'] = '{}'.format(random.randrange(1, 1000))
                outer_goods['selected'] = True if outer_goods['selected'] else False
                if outer_goods.get('sync_time'):
                    outer_goods.pop('sync_time')
                if outer_goods.get('_id'):
                    outer_goods.pop('_id')
                spec_code = outer_goods['spec_code']
                # item_name = outer_goods['itemName']

                # 拿到spu对应的sku数据
                outer_goods_skus = InvSyncGoodsSkuEs().get_all_inv_goods_sku(spec_code)
                for _out in outer_goods_skus:
                    _out['$dataType'] = 'v:inventory.sync$Inventory'
                    _out['$state'] = 2
                    _out['$entityId'] = "{}".format(random.randrange(1, 1000))
                    # _out['itemName'] = item_name
                    _out['selected'] = True if _out['selected'] else False
                    if _out.get('sync_time'):
                        _out.pop('sync_time')

                # 如果是同步sku，过滤那些不需要同步的sku
                filter_skus = []
                if self.FLAG == 'sku' and spu_sku_relation:
                    for re_sku in spu_sku_relation.get(spec_code):
                        for s_index, _sku in enumerate(outer_goods_skus):
                            sku_code = _sku['spec_code']
                            if re_sku == sku_code:
                                filter_skus.append(_sku)
                                sku_list.append(sku_code)
                                break
                            elif s_index == len(outer_goods_skus) - 1:
                                raise Exception('sku:{}在爬虫的数据库中找不到,无法上传此sku的库存'.format(re_sku))

                outer_goods['inventorys'] = {
                    '$isWrapper': True,
                    '$dataType': 'v:inventory.sync$[Inventory]',
                }
                outer_goods['inventorys']['data'] = outer_goods_skus if not spu_sku_relation else filter_skus
                sync_goods.append(outer_goods)

            # 发送上传库存同步的请求
            print('发送上传库存同步的请求')
            sync_inv_obj = InvUpload(sync_goods, sync_config).set_cookie_position(1)
            sync_inv_status, sync_inv_result = CrawlerHelper.get_sync_result(sync_inv_obj)
            if sync_inv_status == 1:
                assert False, '发送上传库存同步的请求失败:{}'.format(sync_inv_result)
            # import json
            # print('sync_inv_result', json.dumps(sync_inv_result))
            if not sync_inv_result.get('response', {}).get('entityStates', {}):
                assert False, '发送上传库存同步的请求失败,获取到的响应不对:{}'.format(sync_inv_result.get('response'))
            # 添加上传库存同步失败的错误详情
            # !!暂时拿不到上传库存同步失败的错误详情
            # inv_err_obj = InventoryErrorMsg().set_cookie_position(1)
            # inv_err_status, inv_err_result = CrawlerHelper.get_sync_result(inv_err_obj)
            # if inv_err_status == 1:
            #     assert False, '部分商品系统库存上传失败,但由于爬虫的问题没有获取失败的详情:{}'.format(sync_inv_result)
            # if not inv_err_result.get('response', {}).get('error'):
            # assert False, '部分商品系统库存上传失败,但是没有正确获取到失败的详情:{}'.format(sync_inv_result)
            # else:
            #     assert False, '库存上传失败详情:{}'.format(inv_err_result.get('response', {}).get('error'))
            print('发送上传库存同步的请求成功')
            sync_time = Date.now().format_es_utc_with_tz()
            return_list = []
            source_list = barcode_list if not spu_sku_relation else sku_list
            for code in source_list:
                return_dict = {
                    'spuBarcode': code,
                    'syncTime': sync_time,
                    'failReason': '',
                    'syncStatus': '0',
                    'flag': self.FLAG,
                }
                return_list.append(return_dict)
            print('发送操作过的商品的数据保存')
            InventorySync().update(return_list, async=True)

        except Exception as e:
            err_msg = '上传库存商品error:{}'.format(e)
            print('err_msg', err_msg)
            print(traceback.format_exc())
            sync_time = Date.now().format_es_utc_with_tz()
            return_list = []
            for code in barcode_list:
                return_dict = {
                    'spuBarcode': code,
                    'syncTime': sync_time,
                    'failReason': err_msg,
                    'syncStatus': '1',
                    'flag': self.FLAG,
                }
                return_list.append(return_dict)
            print('发送操作过的商品的失败数据保存')
            InventorySync().update(return_list, async=True)
        finally:
            # 用于进度记录
            ai_storage_redis.incrby(self.__combined_key, self.STEP)

    def get_upload_inv_config(self):
        """
        获取上传库存的配置
        :return:
        """
        sync_config_list = []
        # 获取库存同步的列表
        inv_list_obj = InventoryConfList().set_cookie_position(1)
        inv_status, inv_list = CrawlerHelper.get_sync_result(inv_list_obj)
        if inv_status == 1:
            assert False, '获取库存同步list失败:{}'.format(inv_list)
        if not inv_list.get('response'):
            assert False, '没有获取到库存同步上传配置的数据'

        inv_list = inv_list.get('response')
        # 组装已开启的库存配置
        for _inv in inv_list:
            q_type = _inv['quantity_type']
            if q_type or (isinstance(q_type, int) and int(q_type) == 0):
                config_dict = {}
                config_dict['storage_uid'] = _inv['storage_uid']
                config_dict['storage_name'] = _inv['storage_name']
                config_dict['shop_uid'] = _inv['shop_uid']
                config_dict['quantity_type'] = _inv['quantity_type']
                config_dict['upload_ratio'] = _inv['upload_ratio']
                config_dict['upload_beyond'] = _inv['upload_beyond']
                sync_config_list.append(config_dict)
        return sync_config_list

    def set_goods_pending(self, spus='', is_all=False):
        """
        把需要操作的库存商品的状态全都改为操作中(1)
        :param spus:
        :param is_all:
        :return:
        """
        sync_time = Date.now().format_es_utc_with_tz()
        if is_all:
            print('全量库存商品的状态更改')
            # 全量更新
            goods = InvSyncGoodsEs().get_all_inv_goods(page_size=100)
            for g in goods:
                return_list = []
                for _g in g:
                    barcode = _g['spec_code']
                    return_msg = {
                        'spuBarcode': barcode,
                        'syncTime': sync_time,
                        'syncStatus': '2',
                        'flag': self.FLAG,
                    }
                    return_list.append(return_msg)
                InventorySync().update(return_list)
            print('全量库存商品的状态更改完成')
        else:
            print('手动同步部分库存商品的状态更改')
            # 部分更新
            if not isinstance(spus, list):
                assert False, '手动同步库存商品传入的spu不是list'
            for spu_list in generator_list(spus, 100):
                return_list = []
                for _spu in spu_list:
                    return_msg = {
                        'spuBarcode': _spu,
                        'syncTime': sync_time,
                        'syncStatus': '2',
                        'flag': self.FLAG,
                    }
                    return_list.append(return_msg)
                InventorySync().update(return_list)
            print('手动同步部分库存商品的状态更改完成')
        print('所有的状态更改都写入了es')

    def get_combine_spu_sku(self, sku_list):
        """
        整合spu对应的sku，返回spu对应sku的所有对应关系
        :param sku_list:
        :return:
        """
        # 找出所有sku对应的spu
        spu_set = set()
        for _sku in sku_list:
            spu_set.add(_sku[:-4])

        # 对应好spu和sku
        spu_sku_relation = {}
        for _sku in sku_list:
            _spu = _sku[:-4]
            if spu_sku_relation.get(_spu):
                spu_sku_relation.get(_spu).append(_sku)
            else:
                spu_sku_relation.setdefault(_spu, [_sku])

        print('spu_set', spu_set)
        print('spu_sku_relation', spu_sku_relation)
        return list(spu_set), spu_sku_relation
