import traceback

from copy import deepcopy

from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from hupun.page.hupun_goods.goods_info_disable import GoodsInfoDisable
from hupun.page.hupun_goods.goods_info_enable import GoodsInfoEnble
from hupun.page.hupun_goods.goods_info_result import GoodsInfoResult
from hupun.page.hupun_goods.goods_information_edit_result import GoodsInfoEditResult
from hupun_operator.page.goods_info.upload_goods import UploadGoods
from mq_handler.base import Base
from pyspider.helper.date import Date
from pyspider.helper.email import EmailSender


class SyncErpGoods(Base):
    """
    同步erp商品数据
    """

    def execute(self):
        print('开始同步erp商品数据')
        self.print_basic_info()

        try:
            self.entry()
        except Exception as e:
            err_msg = '同步erp商品数据发生未知异常:{};'.format(e)
            print(err_msg)
            print('------')
            print(traceback.format_exc())
            print('------')
            self.send_call_back_msg(err_msg, 1)

    def entry(self):
        """
        同步商品的入口
        :return:
        """
        print('同步商品的入口')

        upload_list = []
        error_msg = ''
        data_list = self._data.get('list')

        # 执行添加操作的商品
        print('执行添加操作的商品')
        for _data in data_list:
            spu_barcode = _data.get('spuBarcode')
            sku_barcode = _data.get('skuBarcode')
            data_status = int(_data.get('forbidden'))

            # 优先操作添加操作的商品，跳过关闭操作的商品
            if data_status == 1:
                continue

            # 判断商品是否是启用中
            enable_code, enable_result = self.is_goods_enable(1, sku_barcode)
            if enable_code != 0:
                print_err = '查询启用中的商品:{}失败:爬虫的请求失败了三次;'.format(sku_barcode)
                print(print_err)
                error_msg += print_err
                continue
            # 判断商品是否是停用中
            disable_code, disable_result = self.is_goods_enable(0, sku_barcode)
            if disable_code != 0:
                print_err = '查询停用用中的商品:{}失败:爬虫的请求失败了三次;'.format(sku_barcode)
                print(print_err)
                error_msg += print_err
                continue

            # data_status 是传入的商品操作状态，1 为停用，0 为启用，跟万里牛的状态正好相反
            if data_status == 0:
                print('开始启用商品:{}'.format(sku_barcode))
                # 判断商品是否是启用中
                if enable_result:
                    # 已经启用了，直接返回已成功的消息
                    print('商品:{}已经启用了, 覆盖更新'.format(sku_barcode))
                    upload_list.append(_data)
                elif disable_result:
                    # 商品已停用，把它启用
                    print('商品:{}已停用，把它启用'.format(sku_barcode))
                    # 构造第一层数据
                    first_data = []
                    for _re in disable_result:
                        if spu_barcode == _re.get('goodsCode'):
                            first_data = _re
                    if not first_data:
                        print_err = '查询商品:{}时未在停用列表查询到商品(spu_barcode):{}的信息;'.format(sku_barcode, spu_barcode)
                        print(print_err)
                        error_msg += print_err
                        continue
                    first_data = self.trans_first_data(first_data)
                    # 构造第二层数据
                    second_data = []
                    goods_uid = first_data.get('goodsUid')
                    goods_edit_sku_obj = GoodsInfoEditResult(goods_uid, 0).use_cookie_pool()
                    edit_code, goods_edit_sku = Helper().get_sync_result(goods_edit_sku_obj)
                    if edit_code != 0:
                        print_err = '获取编辑商品信息失败,爬虫请求失败了三次,商品:{};'.format(sku_barcode)
                        print(print_err)
                        error_msg += print_err
                        continue
                    for _e in goods_edit_sku:
                        if sku_barcode == _e.get('specCode'):
                            second_data.append(self.trans_second_data(_e, sku_barcode, 1))
                        else:
                            second_data.append(self.trans_second_data(_e))
                    if not second_data:
                        print_err = '启用商品:{}时,爬虫未查询到(spu_barcode):{}的信息;'.format(sku_barcode, spu_barcode)
                        print(print_err)
                        error_msg += print_err
                        continue
                    # 合并数据
                    first_data['specs'] = {
                        "$isWrapper": True,
                        "$dataType": "v:goods.Goods$[Spec]",
                        "data": second_data
                    }
                    # 启用数据
                    enable_result_obj = GoodsInfoEnble(first_data).use_cookie_pool()
                    enable_code, enable_result = Helper().get_sync_result(enable_result_obj)
                    if enable_code != 0:
                        print_err = '发送启用商品:{}的请求失败,爬虫请求失败了三次;'.format(sku_barcode)
                        print(print_err)
                        error_msg += print_err
                        continue
                    enable_err_msg = enable_result.get('returnValue').get('data')
                    if 'errList' in enable_err_msg:
                        err_msg = enable_err_msg.get('errList')[0].get('error')
                        print_err = '启用商品:{}失败,原因:{};'.format(sku_barcode, err_msg)
                        print(print_err)
                        error_msg += print_err
                    else:
                        # 再次确认一遍是否已经启用
                        enable_code, enable_result = self.is_goods_enable(1, sku_barcode)
                        if enable_code != 0:
                            print_err = '再次确认启用中的商品:{}失败,爬虫的请求失败了三次;'.format(sku_barcode)
                            print(print_err)
                            error_msg += print_err
                            continue
                        if enable_result:
                            print('启用商品:{}成功, 同时覆盖更新'.format(sku_barcode))
                            upload_list.append(_data)
                        else:
                            print_err = '启用商品:{}失败,没有在启用商品列表查询到该商品;'.format(sku_barcode)
                            print(print_err)
                            error_msg += print_err
                else:
                    # 启用中和停用中的都找不到这个商品，发送添加商品的请求
                    print('启用中和停用中的都找不到这个商品，发送添加商品的请求')
                    upload_list.append(_data)

        # 发送添加商品的操作
        print('发送添加商品的操作')
        if upload_list:
            upload_data = {'list': upload_list}
            upload_goods_obj = UploadGoods(upload_data, self._data_id)
            upload_code, upload_goods = Helper().get_sync_result(upload_goods_obj)
            if upload_code != 0:
                print_err = '添加商品失败,爬虫的请求失败了三次;'
                print(print_err)
                error_msg += print_err
            else:
                code = upload_goods.get('code')
                if int(code) == 0:
                    # 成功添加
                    for _up in upload_list:
                        u_sku_barcode = _up.get('skuBarcode')
                        enable_code, enable_result = self.is_goods_enable(1, u_sku_barcode)
                        if enable_code != 0:
                            print_err = '查询启用中的商品:{}失败,爬虫的请求失败了三次;'.format(u_sku_barcode)
                            print(print_err)
                            error_msg += print_err
                        elif not enable_result:
                            print_err = '未查询到商品:{}被启用;'.format(u_sku_barcode)
                            print(print_err)
                            error_msg += print_err
                        else:
                            print('已查询到商品:{}被启用'.format(u_sku_barcode))
                else:
                    # 添加失败
                    print_err = '添加商品失败:{}'.format(upload_goods.get('errMsg'))
                    print(print_err)
                    error_msg += print_err

        # 执行关闭操作的商品
        print('执行关闭操作的商品')
        if not error_msg:
            for _data in data_list:
                spu_barcode = _data.get('spuBarcode')
                sku_barcode = _data.get('skuBarcode')
                data_status = int(_data.get('forbidden'))

                # 操作关闭操作的商品，跳过添加操作的商品
                if data_status == 0:
                    continue

                # 判断商品是否是启用中
                enable_code, enable_result = self.is_goods_enable(1, sku_barcode)
                if enable_code != 0:
                    print_err = '查询启用中的商品:{}失败:爬虫的请求失败了三次;'.format(sku_barcode)
                    print(print_err)
                    error_msg += print_err
                    continue
                # 判断商品是否是停用中
                disable_code, disable_result = self.is_goods_enable(0, sku_barcode)
                if disable_code != 0:
                    print_err = '查询停用用中的商品:{}失败:爬虫的请求失败了三次;'.format(sku_barcode)
                    print(print_err)
                    error_msg += print_err
                    continue

                if data_status == 1:
                    print('开始停用商品:{}'.format(sku_barcode))
                    # 判断商品是否是停用中
                    if disable_result:
                        # 已经停用了，直接返回已成功的消息
                        print('已经停用了，直接返回已成功的消息')
                    elif enable_result:
                        # 商品已启用，把它停用
                        print('商品:{}已启用，把它停用'.format(sku_barcode))
                        # 构造第一层数据
                        first_data = []
                        for _re in enable_result:
                            if spu_barcode == _re.get('goodsCode'):
                                first_data = _re
                        if not first_data:
                            print_err = '停用商品:{}时,爬虫未查询到商品(spu_barcode):{}的信息;'.format(spu_barcode, spu_barcode)
                            print(print_err)
                            error_msg += print_err
                            continue
                        first_data = self.trans_first_data(first_data)
                        # 构造第二层数据
                        second_data = []
                        goods_uid = first_data.get('goodsUid')
                        goods_edit_sku_obj = GoodsInfoEditResult(goods_uid, 1).use_cookie_pool()
                        edit_code, goods_edit_sku = Helper().get_sync_result(goods_edit_sku_obj)
                        if edit_code != 0:
                            print_err = '获取编辑商品信息失败,爬虫请求失败了三次,商品:{};'.format(sku_barcode)
                            print(print_err)
                            error_msg += print_err
                            continue
                        for _e in goods_edit_sku:
                            if sku_barcode == _e.get('specCode'):
                                second_data.append(self.trans_second_data(_e, sku_barcode, 0))
                            else:
                                second_data.append(self.trans_second_data(_e))
                        if not second_data:
                            print_err = '停用商品:{}时,爬虫未查询到(spu_barcode):{}的信息;'.format(sku_barcode, spu_barcode)
                            print(print_err)
                            error_msg += print_err
                            continue
                        # 合并数据
                        first_data['specs'] = {
                            "$isWrapper": True,
                            "$dataType": "v:goods.Goods$[Spec]",
                            "data": second_data
                        }
                        # 停用数据
                        close_result_obj = GoodsInfoDisable(first_data).use_cookie_pool()
                        close_code, close_result = Helper().get_sync_result(close_result_obj)
                        if close_code != 0:
                            print_err = '发送停用商品:{}的请求失败,爬虫请求失败了三次;'.format(sku_barcode)
                            print(print_err)
                            error_msg += print_err
                            continue
                        close_err_msg = close_result.get('returnValue').get('data')
                        if 'errList' in close_err_msg:
                            err_msg = close_err_msg.get('errList')[0].get('error')
                            print_err = '停用商品:{}失败,原因:{};'.format(sku_barcode, err_msg)
                            print(print_err)
                            error_msg += print_err
                        else:
                            # 再次确认一遍是否已经停用
                            disable_code, disable_result = self.is_goods_enable(0, sku_barcode)
                            if disable_code != 0:
                                print_err = '再次确认停用中的商品:{}失败,爬虫的请求失败了三次;'.format(sku_barcode)
                                print(print_err)
                                error_msg += print_err
                                continue
                            if disable_result:
                                print('停用商品:{}成功'.format(sku_barcode))
                            else:
                                print_err = '停用商品:{}失败,没有在停用商品列表查询到该商品;'.format(sku_barcode)
                                print(print_err)
                                error_msg += print_err
                    else:
                        # 启用中和停用中的都找不到这个商品，忽略本次停用操作
                        print_err = '停用商品:{}失败,启用中和停用中都找不到这个商品,跳过;'.format(sku_barcode)
                        print(print_err)
                else:
                    # 传入类型错误，报警
                    print_err = '传入类型错误:{},报警;'.format(data_status)
                    print(print_err)
                    error_msg += print_err

        # 发送消息
        if error_msg:
            self.send_call_back_msg(err_msg=error_msg, status=1)
        else:
            self.send_call_back_msg(status=0)

    def trans_second_data(self, second_data: dict, sku_barcode='', change_status=0):
        """
        处理 second_data 里的数据
        :param second_data: 要更改的第二层谁
        :param sku_barcode: 需要操作关闭或者开启的skubarcode
        :param change_status: 要更改成的状态
        :return:
        """
        second_data['perms']['$dataType'] = 'GoodsPermissions'
        second_data['perms']['$entityId'] = '0'
        second_data['barcodeRef'] = None
        second_data['$dataType'] = 'v:goods.Goods$Spec'
        second_data['$state'] = 2
        second_data['$entityId'] = "0"
        if sku_barcode:
            second_data['status'] = change_status
        return second_data

    def trans_first_data(self, first_data: dict):
        """
        把first_data 里的null值数据进行转换
        :param first_data:
        :return:
        """
        if first_data.get('tagPrice') is None:
            first_data['tagPrice'] = 0
        if first_data.get('wholesalePrice') is None:
            first_data['wholesalePrice'] = 0
        if first_data.get('fractUnitUid') is None:
            first_data['fractUnitUid'] = ""
        if first_data.get('fractUnitName') is None:
            first_data['fractUnitName'] = ""
        first_data['perms']['$dataType'] = 'GoodsPermissions'
        first_data['perms']['$entityId'] = '0'
        first_data['goodsSupplier'] = None
        first_data['barcodeRef'] = None
        first_data['$dataType'] = 'v:goods.Goods$Goods'
        first_data['$state'] = 2
        first_data['$entityId'] = "0"
        return first_data

    def is_goods_enable(self, status, sku_barcode):
        """
        判断商品的启用状态
        :param status: 状态，1、启用中；0、停用中
        :param sku_barcode: 商品 skubarcode
        :return:
        """
        query_goods_obj = GoodsInfoResult(status, sku_barcode).use_cookie_pool()
        code, result = Helper().get_sync_result(query_goods_obj)
        return code, result

    def send_call_back_msg(self, err_msg='', status=1):
        """
        发送返回的消息数据
        :param err_msg: 失败的报错信息，默认为空
        :param status: 消息状态，1 为失败；0 为成功
        :return:
        """
        callback_data = deepcopy(self._data)
        spu_barcode = callback_data.get('list')[0].get('spuBarcode')
        return_msg = {
            "code": status,  # 0：成功 1：失败
            "errMsg": err_msg,  # 如果code为1，请将失败的具体原因返回
            "spuBarcode": spu_barcode
        }
        # 发送失败的消息
        if status != 0 and Helper.in_project_env():
            # 发送失败的消息
            title = '万里牛商品同步操作失败'
            ding_msg = '万里牛商品同步操作失败详情: {}, spu_barcode: {}'.format(err_msg, spu_barcode)
            DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
            # 同时发送邮件通知
            if self._data.get('email'):
                EmailSender() \
                    .set_receiver(self._data.get('email')) \
                    .set_mail_title(title) \
                    .set_mail_content(ding_msg) \
                    .send_email()

        # 发送返回的消息
        print('发送返回的消息数据: {}'.format(return_msg))

        from mq_handler import CONST_MESSAGE_TAG_SYNC_ERP_GOODS_RESULT
        from mq_handler import CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        return_date = Date.now().format()
        msg_tag = CONST_MESSAGE_TAG_SYNC_ERP_GOODS_RESULT
        MQ().publish_message(msg_tag, return_msg, self._data_id, return_date, CONST_ACTION_UPDATE)
