#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2019-01-28 07:10:16
# Project: hupun-operator
from mq_handler import CONST_MESSAGE_TAG_SYNC_ERP_GOODS, CONST_ACTION_UPDATE, CONST_MESSAGE_TAG_PURCHARSE_ADD, \
    CONST_MESSAGE_TAG_PURCHARSE_CLOSE, CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT, CONST_MESSAGE_TAG_PURCHARSE_STOCK_ADD, \
    CONST_MESSAGE_TAG_CATEGORY_DELETE, CONST_MESSAGE_TAG_CATEGORY_UPDATE, CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER, \
    CONST_MESSAGE_TAG_SYNC_ERP_GOODS_RESULT, CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY, \
    CONST_MESSAGE_TAG_SYNC_COMMON_INV, CONST_MESSAGE_TAG_UPDATE_GOODS_RELATION, CONST_MESSAGE_TAG_BLOG_SYNC_ACT, \
    CONST_MESSAGE_TAG_ORDER_SPLIT, CONST_MESSAGE_TAG_ORDER_SKU_RENAME, CONST_MESSAGE_TAG_WAREHOUSE_STORE_SET, \
    CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE, CONST_MESSAGE_TAG_CLOSE_ADD_PURCHASE
from pyspider.helper.date import Date
from pyspider.libs.base_handler import *
from pyspider.libs.mq import MQ


class Handler(BaseHandler):
    crawl_config = {
    }

    def on_start(self):
        self.purchase_close()

    def close_add_purchase(self):
        # 整单关闭再添加采购单
        data = {'data': [
            {"tp_tid": '14019048349435', 'skus': ['23HI019020'], 'remark': 'split_remark007', 'split_type': 1}]}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_CLOSE_ADD_PURCHASE, data, data_id, Date.now().timestamp(), CONST_ACTION_UPDATE)

    def warehouse_store_set(self):
        # 例外店铺的店铺和仓库对应关系设置
        data = {
            'data': [{'channel': 'icy旗舰店', 'storage_code': 'SPD0000253'}, {'channel': 'ICY奥莱', 'storage_code': '012'},
                     {'channel': 'ICY唯品会', 'storage_code': 'SPD0000253'}, {'channel': '穿衣助手旗舰店', 'storage_code': '012'},
                     {'channel': 'iCY设计师集合店', 'storage_code': '012'},
                     {'channel': 'ICY设计师平台', 'storage_code': 'SPD0000253'},
                     {'channel': 'ICY小红书', 'storage_code': '012'}]}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_WAREHOUSE_STORE_SET, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def update_order_spilit(self):
        # 拆分订单
        data = {'data': [
            {"tp_tid": '14019048349435', 'skus': ['23HI019020'], 'remark': 'split_remark007', 'split_type': 1}]}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_ORDER_SPLIT, data, data_id, Date.now().timestamp(), CONST_ACTION_UPDATE)

    def update_order_sku_rename(self):
        # 订单商品sku改名
        data = {'data': [{"tp_tid": '574496535480069528'}]}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_ORDER_SKU_RENAME, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def update_goods_relation(self):
        # 更新erp的商品对应关系
        data = {"shop_name": ['[淘宝]ICY设计师平台']}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_UPDATE_GOODS_RELATION, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def inv_sync_manual(self):
        # 手动更新各渠道库存
        data = {"spu": ['19300D0004'], "isAll": 0, 'flag': 'spu'}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def demo_msg_inv_config(self):
        # 库存同步的通用配置更改
        data = {'data': [
            {
                "storage_uid": "21130C06EE723229AC379095BF0305A8",
                "shop_name": "iCY设计师集合店",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "21130C06EE723229AC379095BF0305A8",
                "shop_name": "穿衣助手旗舰店",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 90,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "21130C06EE723229AC379095BF0305A8",
                "shop_name": "达人选款订单通道",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 90,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "21130C06EE723229AC379095BF0305A8",
                "shop_name": "ICY小红书",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 90,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "21130C06EE723229AC379095BF0305A8",
                "shop_name": "ICY奥莱",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "icy旗舰店",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "达人选款订单通道",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存+在途库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "D1E338D6015630E3AFF2440F3CBBAFAD",
                "shop_name": "ICY唯品会",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
            {
                "storage_uid": "FBA807A72474376E8CFBBE9848F271B2",
                "shop_name": "ICY设计师平台",
                'open_auto': True,  # 是否打开自动上传
                "quantity_type": "可用库存",  # 需要同步的具体库存
                "upload_ratio": 100,  # 同步的库存比例
                "upload_beyond": 0  # 同步的库存添加数量
            },
        ]}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_SYNC_COMMON_INV, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def purchase_stock(self):
        recv_data = {'storeHouseCode': '020', 'supplierCode': '0758', 'tgPurchaseBill': '201905170205',
                     'erpPurchaseBill': 'CD201907300004', 'goodsList': [{'skuBarcode': '1922A10009W703', 'count': '1'}]}
        data_id = '111'
        MQ().publish_message(CONST_MESSAGE_TAG_PURCHARSE_STOCK_ADD, recv_data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def purchase_close(self):
        data = {
            "erpPurchaseNo": "CD202003070030",  # 万里牛采购单号
            "formId": '201905210081',
            "list": [
                {
                    "supplierCode": "0423",  # 供应商名称
                    "skuBarcode": "1918A10002C902",  # 商品编码(sku)
                    "purchaseCount": 2,  # 商品采购数量
                    "arriveCount": 2,  # 商品已入库数
                    "closeCount": 1  # 商品关闭数
                }
            ]
        }
        data1 = {'erpPurchaseNo': 'CD202003070030', 'formId': '202003090033', 'list': [
            {'supplierName': '嘉兴市沃普服饰有限公司', 'supplierCode': '0423', 'purchaseCount': 1, 'arriveCount': 0,
             'skuBarcode': '19490C0022W122', 'closeCount': 1}]}

        data_id = '111'
        MQ().publish_message(CONST_MESSAGE_TAG_PURCHARSE_CLOSE, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def purchase_add(self):
        # 添加采购单
        data1 = {'list': [
            {'purchaseNo': '201908074', 'supplierCode': '0684', 'storageCode': '020', 'skuBarcode': '1907010037C903',
             'purchaseCount': 10, 'price': '155.0000', 'remark': 'testpuadd'}], 'type': 2,
                 'warehouseId': '202003050006'}
        data = {
            "erpPurchaseNo": "CD201905070011",  # erp采购单号
            "changedNum": 1,  # 变更的数量 可以为正负
            "quantity": 1,  # 库存结余
            "skuBarcode": "1919N00002W402"  # sku
        }
        data_id = data.get('erpPurchaseNo')
        # MQ().publish_message(CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT, data, data_id, Date.now().timestamp(),
        #                     CONST_ACTION_UPDATE)
        MQ().publish_message(CONST_MESSAGE_TAG_PURCHARSE_ADD, data1, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def send_goods_info_msg(self):
        data = {'list':
            [
                {
                    "spuBarcode": "chen(test)",  # 天鸽：商品编码SPU
                    "name": "测试上传(test)",  # 商品名称
                    "skuBarcode": "chen(test)M02",  # 规格编码
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
                    "material": "棉(test)",  # 材质成分
                    'forbidden': 0
                }
            ]
        }
        data_id = '111'
        MQ().publish_message(CONST_MESSAGE_TAG_SYNC_ERP_GOODS, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def catetory_delete(self):
        data_id = '154052243339'
        data = {'erpGoodsCategoryId': ['6B43EB9262CF31B895AB977DB0E88F20']}
        MQ().publish_message(CONST_MESSAGE_TAG_CATEGORY_DELETE, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def catetory_update(self):
        data_id = '154052243339'
        parent_id = '-1'
        name = 'testxiiadsfx0234'
        uid = ''
        data = {'erpGoodsCategoryId': uid, 'erpParentId': parent_id, 'name': name}
        MQ().publish_message(CONST_MESSAGE_TAG_CATEGORY_UPDATE, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def supplier_update(self):
        data = {
            "erpSupplierId": "",  # ERP中供应商的ID, 如有该字段则表示 修改，否则表示 新增
            "name": "test01021"
        }
        data_id = '234'
        MQ().publish_message(CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def sync_blog_keywords(self):
        # 抓取微博的关键词
        data = {'type': 1, 'keywords': ['游戏开发'], 'contentType': 2}
        data_id = '1112'
        MQ().publish_message(CONST_MESSAGE_TAG_BLOG_SYNC_ACT, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)

    def purchase_whole_close(self):
        # 整单关闭采购单
        data = {'erpPurchaseNo': '020xxx', 'formId': '0758', 'purchaseId': '201905170205'}
        data_id = '111'
        MQ().publish_message(CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE, data, data_id, Date.now().timestamp(),
                             CONST_ACTION_UPDATE)
