import copy
import uuid

from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from hupun_operator.config import PARSED_TYPE
from hupun_operator.page.common_get import CommonGet
from pyspider.libs.base_crawl import *
from urllib import parse
from pyspider.helper.excel import Excel
from cookie.model.data import Data as CookieData


class UploadGoods(BaseCrawl):
    """
    上传商品数据到erp
    """
    PATH = '/dorado/uploader/fileupload'
    # 总仓
    STORAGE_UID = 'D1E338D6015630E3AFF2440F3CBBAFAD'

    # 这个是上传表格的时候用到的（好像必须是这个ID，要不然会报错）
    CM = 'D1E338D6015630E3AFF2440F3CBBAFAD'

    def __init__(self, data, data_id):
        super(UploadGoods, self).__init__()
        self.__data = copy.deepcopy(data)
        self.__data_id = data_id

    def crawl_builder(self):
        excel = self.get_excel()
        # TODO 商品数据的组装改成真实的数据
        for d in self.__data['list']:
            excel.add_data(self.value_to_erp(d))
        return CrawlBuilder() \
            .set_url('{}{}#{}'.format(config.get('hupun', 'service_host'), self.PATH, self.__data_id)) \
            .set_upload_files_kv('file', ('file.xlsx', excel.execute())) \
            .set_task_id(uuid.uuid4()) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[1][0])) \
            .set_post_data_kv('storageUid', self.STORAGE_UID) \
            .set_post_data_kv('encodingImportSwitch', 1) \
            .set_post_data_kv('exec', 'importGoods') \
            .set_post_data_kv('cm', self.CM) \
            .set_post_data_kv('op', 'op') \
            .set_post_data_kv('sn', 'sn') \
            .set_post_data_kv('tk', 'tk') \
            .set_post_data_kv('_fileResolver', 'uploadInterceptor#process') \
            .set_kwargs_kv('validate_cert', False)

    def parse_response(self, response, task):
        result = parse.unquote(response.text).strip('"').split('|')
        if result[2]:
            doc = CommonGet(result[2], PARSED_TYPE).get_result()
            result_msg = doc.replace(' ', '').replace('\n', '')

            return_msg = {
                "code": 1,  # 0：成功 1：失败
                "errMsg": result_msg  # 如果code为1，请将失败的具体原因返回
            }
        elif result[1]:
            return_msg = {
                "code": 1,  # 0：成功 1：失败
                "errMsg": result[1]  # 如果code为1，请将失败的具体原因返回
            }
        else :
            return_msg = {
                "code": 0,  # 0：成功 1：失败
                "errMsg": ''  # 如果code为1，请将失败的具体原因返回
            }
        return return_msg

    def value_to_erp(self, data):
        """
        把数据转为erp上传的对应字段
        :param data:
        :return:
        """
        # year_data = str(data.get('year', '')) + '年' + data.get('season', '') + '季'
        the_list = {
            'spu01': data.get('spuBarcode', ''),
            'name': data.get('name', ''),
            'sku': data.get('skuBarcode', ''),
            'color': data.get('color', ''),
            'size': data.get('size', ''),
            'spu02': data.get('supplierGoodsNo', ''),
            'category': data.get('categoryName', ''),
            'purchasePrice': data.get('newPurchasePrice', 0),
            'unit': data.get('unit', ''),
            # 'image1': data.get('image1', ''),
            # 'image2': data.get('image2', ''),  # 只处理image2，image1和image3 都不用处理; 20200609更新：暂时停止所有图片的上传，因为万里牛那边有bug
            # 'image3': data.get('image3', ''),
            'designer': data.get('designerName', ''),
            'originPlace': data.get('productLocation', ''),
            'execStandardName': data.get('execStandardName', ''),
            'securityTypeName': data.get('securityTypeName', ''),
            'level': data.get('levelName', ''),
            'material': data.get('material', ''),
        }
        return the_list

    def get_excel(self):
        """
        定义表头及字段名
        :return:
        """
        return Excel() \
            .add_header('spu01', '商品编码') \
            .add_header('name', '商品名称') \
            .add_header('sku', '规格编码') \
            .add_header('color', '规格值1') \
            .add_header('size', '规格值2') \
            .add_header('sku', '条码') \
            .add_header('NONE', '关键字') \
            .add_header('spu01', '货号') \
            .add_header('NONE', '重量(kg)') \
            .add_header('NONE', '长(cm)') \
            .add_header('NONE', '宽(cm)') \
            .add_header('NONE', '高(cm)') \
            .add_header('NONE', '体积(m³)') \
            .add_header('NONE', '期初库存') \
            .add_header('NONE', '期初成本均价') \
            .add_header('NONE', '货位编码') \
            .add_header('category', '分类') \
            .add_header('NONE', '品牌') \
            .add_header('NONE', '开票名称') \
            .add_header('NONE', '销项税') \
            .add_header('NONE', '进项税') \
            .add_header('NONE', '标准售价') \
            .add_header('NONE', '批发价') \
            .add_header('purchasePrice', '参考进价') \
            .add_header('NONE', '吊牌价') \
            .add_header('unit', '单位') \
            .add_header('image2', '图片1') \
            .add_header('image1', '图片2') \
            .add_header('image3', '图片3') \
            .add_header('image4', '图片4') \
            .add_header('NONE', '备注') \
            .add_header('NONE', '消耗周期(天)') \
            .add_header('originPlace', '产地') \
            .add_header('designer', '设计师') \
            .add_header('execStandardName', '执行标准') \
            .add_header('securityTypeName', '安全技术类别') \
            .add_header('level', '等级') \
            .add_header('material', '材质成分') \
            .add_header('spu02', '供应商货号') \
            .add_header('NONE', '商品税型') \
            .add_header('NONE', '增值税率') \
            .add_header('NONE', '层级价格') \
            .add_header('NONE', '消费税1') \
            .add_header('NONE', '消费税2')
