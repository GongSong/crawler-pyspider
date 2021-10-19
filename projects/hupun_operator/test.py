import json
import random
import traceback
import unittest
from copy import deepcopy

from hupun.page.purchase_order_goods_result import PurOrderGoodsResult
from hupun.page.purchase_order_query_result import POrderQueResult
from hupun.page.purchase_order_result import PurchaseOrderResult
from hupun_api.page.purchase_order_close import PurchaseOrderClose
from hupun_operator.config import *
from hupun_operator.page.inventory.inventory_conf_list import InventoryConfList
from hupun_operator.page.inventory.inventory_sync_goods import InvSyncGoods
from hupun_operator.page.inventory.inventory_sync_goods_sku import InvSyncGoodsSku
from hupun_operator.page.inventory.inventory_sync_operate import InvSyncOperate
from hupun_operator.page.inventory.inventory_upload import InvUpload
from hupun_operator.page.order_split.order_number_query import OrderNumQuery
from hupun_operator.page.purchase.close_audit import CloseAudit
from hupun_operator.page.purchase.pur_order_close_status import PurOrderCloseStatus
from hupun_operator.page.purchase.submit_audit import SubmitAudit
from hupun_operator.page.goods_info.upload_goods import UploadGoods
from hupun_slow_crawl.model.es.inventory_sync_goods_es import InvSyncGoodsEs
from hupun_slow_crawl.model.es.inventory_sync_goods_sku_es import InvSyncGoodsSkuEs
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.date import Date


class Test(unittest.TestCase):
    def test_goods(self):
        upload_list = [
            {
                "spuBarcode": "00002(test)",  # 天鸽：商品编码SPU
                "name": "测试上传(test)",  # 商品名称
                "skuBarcode": "0000202(test)",  # 规格编码
                "color": "白色(test)",  # 天鸽：颜色
                "size": "XL(test)",  # 天鸽：尺码
                "supplierGoodsNo": "0000202(test)",  # 天鸽：供应商货号
                "categoryName": "分类1(test)",  # 天鸽:二级类目
                "newPurchasePrice": "20",  # 天鸽:采买单价
                "unit": "件(test)",  # 单位
                "image1": "https://image3(test)",  # 图片1
                "image2": "https://image3.ichuanyi.cn/gro(test)",  # 图片2
                "image3": "https://image3(test)",  # 图片3
                "designerName": "设计师(test)",  # 设计师
                "productLocation": "产地(test)",  # 产地
                "year": 2019,  # 年份
                "season": "春",  # 季节
                "execStandardName": "高(test)",  # 执行标准
                "securityTypeName": "良好(test)",  # 安全技术类别
                "levelName": "等级01(test)",  # 等级
                "material": "棉(test)"  # 材质成分
            }
        ]
        upload_data = {'list': upload_list}
        result = UploadGoods(upload_data, "234234ss33").get_result()
        print('result', result)

    def _test_purchase(self):
        data_id = ''
        data = {
            'sku': '0042',
            'pchsSum': 10,
            'price': 2333.25,
            'supplier_name': 'test006',
        }
        # 上传采购订单的Excel文件
        # status, msg = UploadPurchase(data, data_id).get_result()
        # return
        # if status == 1:

        # 发送错误消息
        # return
        #     err_msg = msg['data'][0]['content']
        # else:
        #     bill_code = msg['data'][0]['billCode']
        bill_code = 'CD201904240046'
        print('提交订单bill_code: {}'.format(bill_code))

        # 提交订单，获取采购订单号对应的结构化数据
        first_data = self.fetch_bill_data(bill_code)
        if not first_data:
            err_msg = '未获取到采购订单: {}, 同步失败，中断并退出。'.format(bill_code)
            # 删除同步失败的采购订单
            # self.close_purchase_bill(bill_code)
            print(err_msg)
            return

        # 判断订单状态
        bill_status = int(first_data['status'])
        if bill_status == PENDING:
            # 等待中，提交审核
            print('等待中，提交审核')
            result = SubmitAudit(first_data).get_result()
            print('等待中，提交审核result: {}'.format(result))
            if result:
                # 有事发生，处理事故
                print('有事发生，处理事故')
                # 删除同步失败的采购订单
                # self.close_purchase_bill(bill_code)
                return
            else:
                print('提交成功，继续流程')
        else:
            print('流程不正确，退出')
            # 删除同步失败的采购订单
            # self.close_purchase_bill(bill_code)
            # return

        second_data = self.fetch_bill_data(bill_code)
        bill_status = int(second_data['status'])
        if bill_status == AUDITTING:
            # 审核中，对比数据后，确认数据通过与否
            print('审核中，对比数据后，确认数据通过与否')
            second_data = self.fetch_bill_data(bill_code)
            status, msg = self.compare_dict(data, second_data)
            if status == 1:
                print('抓取的数据缺少字段:{}'.format(','.join(msg)))
                # 删除同步失败的采购订单
                # self.close_purchase_bill(bill_code)
                # return

            # 通过了字段对比，审核通过
            result = SubmitAudit(second_data).get_result()
            if result:
                # 有事发生，处理事故
                print('有事发生，处理事故')
                # 删除同步失败的采购订单
                # self.close_purchase_bill(bill_code)
                return
            else:
                print('通过了审核，返回单据编号: {}'.format(bill_code))
        else:
            print('流程不正确，退出，status: {}'.format(bill_status))
            # 删除同步失败的采购订单
            # self.close_purchase_bill(bill_code)
            return

    def _test_purchase_close(self):
        """
        采购订单的关闭同步
        beforeUpdate  断点
        :return:
        """
        # bill_code = 'CD201904160031'
        bill_code = 'CD201904180018'
        # close_msg = self.close_purchase_bill(bill_code, level=2, bill_data={}, bill_sku_data={})
        # print('close_msg:{}\n'.format(close_msg))
        # return
        result = POrderQueResult(bill_code).set_start_time(Date.now().plus_days(-30).format()).get_result()[0]
        if result:
            print('result: {}, \n'.format(result))
            bill_uid = result.get('bill_uid', '')
            # bill_uid = '2342sdfsdfasdfase'
            # 有数据，获取采购单的sku级别的数据
            sku_result = PurOrderGoodsResult(bill_uid).get_result()[0]
            if sku_result:
                print('sku_result: {}\n'.format(sku_result))
                # 有数据，获取采购单的sku级别的数据
                # if len(sku_result) != count:
                #     print('报警')
                # for _res in sku_result:
                #     status, msg = self.compare_dict(data2, _res)
                #     if status == 1:
                #         print('报警')
                #         return
                # 关闭对应的sku单
                # 数据通过，删除数据
                result_copy = deepcopy(result)
                result_two_details = deepcopy(sku_result)

                result_two_details['$dataType'] = "v:purchase.bill$pchs_detail"
                result_two_details['$state'] = 2
                result_two_details['$entityId'] = "0"
                result_two_details['$oldData'] = sku_result
                result_two_details['expecte_date'] = result_two_details['expecte_date'] + 'T00:00:00Z'
                result_two_details['status'] = 3
                result_copy['$dataType'] = "v:purchase.bill$purchaseBill"
                result_copy['$state'] = 2
                result_copy['$entityId'] = "0"
                result_copy['bill_date'] = result_copy['bill_date'] + 'T00:00:00Z'
                result_copy['details'] = {
                    "$isWrapper": True,
                    "$dataType": "v:purchase.bill$[pchs_detail]",
                    "data": [result_two_details]
                }
                result_copy['$oldData'] = result

                sku_re_copy = deepcopy(sku_result)
                sku_re_copy['$dataType'] = "v:purchase.bill$pchs_detail"
                sku_re_copy['$state'] = 2
                sku_re_copy['$entityId'] = "0"
                sku_re_copy['expecte_date'] = sku_re_copy['expecte_date'] + 'T00:00:00Z'
                sku_re_copy['status'] = 3
                sku_re_copy['$oldData'] = sku_result

                close_msg = self.close_purchase_bill(bill_code, level=2, bill_data=result_copy,
                                                     bill_sku_data=sku_re_copy)
                if 'error' in close_msg:
                    print('发送关闭同步失败的消息以及原因')
                else:
                    print('关闭成功')
            else:
                print('发送关闭同步失败的消息以及原因')

            # 比对数据
        else:
            # 没有数据，报警
            print('发送关闭同步失败的消息以及原因')

    def _fetch_bill_data(self, bill_code):
        """
        基于单据编号返回对应的代购订单数据
        :param bill_code:
        :return:
        """
        result = PurchaseOrderResult(bill_code) \
            .set_start_time(Date.now().plus_days(-7).format()) \
            .set_end_time(Date.now().format()) \
            .set_page_size(200) \
            .get_result()
        for _r in result:
            if _r['bill_code'] == bill_code:
                return _r
        return {}

    def _close_purchase_bill(self, bill_code='', level=1, bill_data='', bill_sku_data=''):
        """
        根据采购单据编码关闭采购订单;
        这个关闭的是第一层的采购订单（第一层指的是直接查询万里牛返回的面板信息）
        :param bill_code:
        :param level:
        :param bill_data:
        :param bill_sku_data:
        :return:
        """
        if level == 1:
            result = PurchaseOrderClose().set_param('bill_code', bill_code).get_result()
        else:
            result = CloseAudit(bill_data, bill_sku_data).get_result()
        return result

    def _compare_dict(self, input_dict, crawl_dict):
        """
        比较两个dict数据是否一样
        :param input_dict:
        :param crawl_dict:
        :return:
        """
        import json
        print('input_dict: {}'.format(input_dict))
        print('crawl_dict: {}'.format(json.dumps(crawl_dict)))
        lack_data = list()
        for k, v in input_dict.items():
            if k == 'pchsSum' or k == 'price':
                sum = input_dict.get('pchsSum', 0) * float(input_dict.get('price', 0))
                if sum != float(crawl_dict.get('goods_sum', 0)):
                    lack_data.append(k)
            elif k == 'sku':
                continue
            elif crawl_dict.get(k) != v:
                lack_data.append(k)
        if lack_data:
            return 1, lack_data
        else:
            return 0, ''

    def _test_purchase_order_close_status(self):
        """
        关闭采购跟单时刷新该采购跟单对应的采购订单数据 的单元测试
        :return:
        """
        bill_uid = 'A19C34CC2BFB3FB68B48504CED741654'
        data = PurOrderCloseStatus(bill_uid).set_cookie_position(1).get_result()
        print('data', data)

    def _test_inventory_config(self):
        """
        库存通用配置的更改
        !!! 已完成开发
        :return:
        """

        received_data = {'data': [
            {
                "storage_name": "研发测试仓",
                "shop_name": "ICY设计师平台",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "实际库存",  # 需要同步的具体库存
                "upload_ratio": 80,  # 同步的库存比例
                "upload_beyond": 5  # 同步的库存添加数量
            },
            {
                "storage_name": "总仓",
                "shop_name": "iCY设计师集合店",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_name": "总仓",
                "shop_name": "icy旗舰店",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_name": "总仓",
                "shop_name": "穿衣助手旗舰店",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_name": "总仓",
                "shop_name": "ICY唯品会",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_name": "总仓",
                "shop_name": "ICY小红书",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_name": "总仓",
                "shop_name": "ICY奥莱",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
        ]}
        received_data = [dict(t) for t in set([tuple(d.items()) for d in received_data.get('data')])]

        # 获取库存同步的列表
        inv_list_obj = InventoryConfList().set_cookie_position(1)
        inv_status, inv_list_result = CrawlerHelper.get_sync_result(inv_list_obj)
        if inv_status == 1:
            print('获取库存同步list失败:{}'.format(inv_list_result))
            return
        self.sync_inventory_conf_args(inv_list_result['response'], received_data)

    def _test_upload_inventory(self):
        """
        操作上传库存的单元测试
        :return:
        """
        # 同步配置
        sync_config = self.get_upload_inv_config()
        # 初始化数据
        page = 1
        goods = InvSyncGoodsEs().get_all_inv_goods()
        for g in goods:
            try:
                print('开始操作第:{}页的上传库存商品'.format(page))
                sync_goods = []
                for _g in g:
                    print('spec_code', _g['spec_code'])
                    outer_goods = deepcopy(_g)
                    outer_goods['$dataType'] = 'v:inventory.sync$Inventory'
                    outer_goods['$entityId'] = '{}'.format(random.randrange(1, 1000))
                    if outer_goods.get('sync_time'):
                        outer_goods.pop('sync_time')
                    spec_code = outer_goods['spec_code']
                    outer_goods_skus = InvSyncGoodsSkuEs().get_all_inv_goods_sku(spec_code)
                    for _out in outer_goods_skus:
                        _out['$dataType'] = 'v:inventory.sync$Inventory'
                        _out['$state'] = 2
                        _out['$entityId'] = "{}".format(random.randrange(1, 1000))
                        if _out.get('sync_time'):
                            _out.pop('sync_time')
                    outer_goods['inventorys'] = {
                        '$isWrapper': True,
                        '$dataType': 'v:inventory.sync$[Inventory]',
                        'data': outer_goods_skus
                    }
                    sync_goods.append(outer_goods)

                # 发送上传库存同步的请求
                print('发送上传库存同步的请求')
                sync_inv_obj = InvUpload(sync_goods, sync_config)
                sync_inv_status, sync_inv_result = CrawlerHelper.get_sync_result(sync_inv_obj)
                if sync_inv_status == 1:
                    assert False, '发送上传库存同步的请求失败:{}'.format(sync_inv_result)
                if not sync_inv_result.get('response', {}).get('entityStates', {}):
                    assert False, '发送上传库存同步的请求失败,获取到的响应不对:{}'.format(sync_inv_result.get('response'))
                print('发送上传库存同步的请求成功')
            except Exception as e:
                print('第:{}页操作上传库存商品失败:{}'.format(page, e))
                print(traceback.format_exc())
            page += 1

    def _test_order_number_query(self):
        """
        订单审核页面根据订单号查询需要拆分的订单
        :return:
        """
        tp_tid = 'P533537119798527131'
        OrderNumQuery(tp_tid).get_result()

    def get_req_args(self, sync_config, goods_list):
        """
        构造库存同步操作的结构参数
        :param sync_config: 库存同步详情数据
        :param goods_list: 商品sku详情列表
        :return:
        """
        # 保存构造商品的的list
        sku_result_list = []
        # 组装spu商品信息
        for goods_code in goods_list:
            print('添加商品:{}的信息'.format(goods_code))

            # 根据商品编码获取库存同步里的商品信息
            goods_obj = InvSyncGoods(goods_code)
            g_status, goods_result = CrawlerHelper.get_sync_result(goods_obj)
            if g_status == 1:
                assert False, ('获取商品:{}失败, err:{}'.format(goods_code, goods_result))
            if not goods_result:
                assert False, ('获取商品:{}失败, err:未查询到该商品'.format(goods_code))
            goods_result = goods_result[0]
            print('goods_result', goods_result, '\n')
            # 获取商品对应的所有sku信息
            goods_uid = goods_result['itemID']
            goods_sku_obj = InvSyncGoodsSku(goods_uid)
            g_sku_status, goods_sku_result = CrawlerHelper.get_sync_result(goods_sku_obj)
            if g_sku_status == 1:
                assert False, ('获取商品sku:{}失败, err:{}'.format(goods_code, goods_sku_result))
            if not goods_sku_result:
                assert False, ('获取商品sku:{}失败, err:未能在万里牛展开该商品'.format(goods_code))
            print('goods_sku_result', goods_sku_result, '\n')
            for _sku in goods_sku_result:
                _sku['$dataType'] = 'v:inventory.sync$Inventory'
                _sku['$state'] = '2'
                _sku['$entityId'] = '0'

            # 构造请求数据块
            print('开始构造请求数据块')
            goods_result['$dataType'] = 'v:inventory.sync$Inventory'
            goods_result['$entityId'] = '0'
            goods_result['inventorys'] = {
                '$isWrapper': True,
                '$dataType': 'v:inventory.sync$[Inventory]',
                'data': goods_sku_result
            }
            sku_result_list.append(goods_result)

        req_shell = {
            "action": "resolve-data",
            "context": {},
            "dataResolver": "inventoryInterceptor#saveInventory",
            "dataItems": [
                {
                    "alias": "dsInventory",
                    "data": {
                        "$isWrapper": True,
                        "$dataType": "v:inventory.sync$[Inventory]",
                        "data": sku_result_list
                    },
                    "refreshMode": "value",
                    "autoResetEntityState": True
                }
            ],
            "parameter": {
                "syn_config": sync_config,
                "view": "inventory.sync",
            }
        }

    def sync_inventory_conf_args(self, inv_list, received_data):
        """
        获取库存通用配置更改的请求参数结构体
        :param inv_list: 库存手动（自动）同步详情的所有数据
        :param received_data: 接收到的库存配置信息
        :return:
        """
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
        # print('sync_data', json.dumps(sync_data))
        ope_obj = InvSyncOperate(sync_data).set_cookie_position(1)
        ope_status, ope_result = CrawlerHelper.get_sync_result(ope_obj)
        if ope_status == 1:
            assert False, '操作更改库存同步配置失败:{}'.format(ope_result)
        if not ope_result.get('response', {}).get('entityStates', {}):
            assert False, '操作更改库存同步配置失败,获取到的响应不对:{}'.format(ope_result)
        print('ope_result', ope_result)
        print('更改本次库存同步的配置成功')

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

    def _test_extra_store_setting(self):
        """
        【仓库匹配】的例外店铺设置测试
        :return:
        """
        # 输入信息
        input_shop_name = 'ICY奥莱'
        # storage_code = '020'
        storage_code = 'SPD0000253'


if __name__ == '__main__':
    unittest.main()
