import copy
import uuid

from pyspider.libs.base_crawl import *
from alarm.page.ding_talk import DingTalk
from urllib import parse
from pyspider.helper.excel import Excel
from cookie.model.data import Data as CookieData
from hupun_operator.page.common_post import CommonPost
from hupun_operator.page.common_get import CommonGet
from hupun_operator.page.download_excel_detect import DownloadExcelDetect


class UploadPurchase(BaseCrawl):
    """
    上传商品数据到erp 的采购订单
    """
    PATH = '/dorado/uploader/fileupload'

    # 文件名
    upload_name = '采购快速导入文件.xls'

    # 这个是上传表格的时候用到的（好像必须是这个ID，要不然会报错）
    CM = 'D1E338D6015630E3AFF2440F3CBBAFAD'

    def __init__(self, data, storage_uid, storage_name):
        super(UploadPurchase, self).__init__()
        self.__data = copy.deepcopy(data)
        self.__storage_name = storage_name
        self.__storage_uid = storage_uid

    def crawl_builder(self):
        excel = self.get_excel()
        # TODO 商品数据的组装改成真实的数据
        for _d in self.__data.get('list'):
            excel.add_data(self.value_to_erp(_d))
        return CrawlBuilder() \
            .set_url('{}{}'.format(config.get('hupun', 'service_host'), self.PATH)) \
            .set_upload_files_kv('file', ('file.xlsx', excel.execute())) \
            .set_task_id(md5string(uuid.uuid4())) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[0][0])) \
            .set_post_data_kv('storageUid', self.__storage_uid) \
            .set_post_data_kv('storageName', self.__storage_name) \
            .set_post_data_kv('name', self.upload_name) \
            .set_post_data_kv('exec', 'importBillB') \
            .set_post_data_kv('cm', self.CM) \
            .set_post_data_kv('op', 'op') \
            .set_post_data_kv('sn', 'sn') \
            .set_post_data_kv('tk', 'tk') \
            .set_post_data_kv('checkType', 'all') \
            .set_post_data_kv('remark', self.__data.get('list')[0].get('remark')) \
            .set_post_data_kv('_fileResolver', 'uploadInterceptor#process') \
            .set_kwargs_kv('validate_cert', False)

    def parse_response(self, response, task):
        result = parse.unquote(response.text).strip('"').split('|')
        status = 0
        print(result)
        # 如果有html类型的错误地址，说明整个表格导入都失败了
        if result[2]:
            doc = CommonGet(result[2]).get_result()
            status = 1
            error_msg = doc.replace(' ', '').replace('\n', '')
            msg = error_msg
            print('导入错误: ', msg)
        else:
            # 获取当前数据导入的结果（导入结果只能是导入成功后，通过这个查询接口拿）
            import_result = CommonPost(CommonPost.IMPORT_PURCHASE_RESULT).get_result()
            bill_code = import_result.get('data')[0].get('billCode')
            print('导入结果: ', import_result)
            print('导入结果的 bill_code: ', bill_code)
            # 获取当前数据导入的错误excel的key
            import_err_k = CommonPost(CommonPost.IMPORT_PURCHASE_ERROR_K).get_result()
            print('错误excel的key: ', import_err_k)
            # 根据错误excel的key下载excel
            err_result = DownloadExcelDetect(import_err_k['data']['msg']).get_result()
            error_msg = err_result[0].get('error', '') if err_result else ''
            print('错误数据: ', err_result)
            print('错误数据error_msg: ', error_msg)
            # 返回错误数据
            if error_msg:
                status = 1
                msg = error_msg + ';bill:{}'.format(bill_code)
            else:
                msg = import_result
        return status, msg

    def value_to_erp(self, data):
        """
        把数据转为erp上传的对应字段
        :param data:
        :return:
        """
        the_list = {
            'sku': data.get('skuBarcode', ''),
            # 'goods_name': data.get('goods_name', ''),
            'count': data.get('purchaseCount', ''),
            'price': data.get('price', ''),
            'supplier': data.get('supplierName', ''),
            'arrivalDate': data.get('arrivalDate', ''),
        }
        return the_list

    def get_excel(self):
        """
        定义表头及字段名
        :return:
        """
        return Excel() \
            .add_header('sku', '商品编码') \
            .add_header('sku', '商品条码') \
            .add_header('goods_name', '商品名称') \
            .add_header('NONE', '规格名称') \
            .add_header('count', '<必填>采购数量') \
            .add_header('NONE', '单位') \
            .add_header('price', '<必填>单价') \
            .add_header('NONE', '折扣率(%)') \
            .add_header('cycle', '采购周期') \
            .add_header('arrivalDate', '到货日期') \
            .add_header('NONE', '商品备注') \
            .add_header('supplier', '供应商') \
            .add_header('salesman', '业务员账号') \
            .add_header('NONE', '结算方式')
