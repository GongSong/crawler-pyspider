import copy
import uuid

from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from hupun_slow_crawl.page.supplier import Supplier
from hupun.page.supplier_result import SupplierResult
from hupun_operator.config import PARSED_TYPE
from hupun_operator.page.common_get import CommonGet
from pyspider.helper.date import Date
from pyspider.helper.email import EmailSender
from pyspider.libs.base_crawl import *
from urllib import parse
from pyspider.helper.excel import Excel
from cookie.model.data import Data as CookieData


class UploadSupplier(BaseCrawl):
    """
    上传 供应商数据 到erp
    """
    PATH = '/dorado/uploader/fileupload'

    # 这个是上传表格的时候用到的（好像必须是这个ID，要不然会报错）
    CM = 'D1E338D6015630E3AFF2440F3CBBAFAD'

    def __init__(self, data, data_id):
        super(UploadSupplier, self).__init__()
        self.__data = copy.deepcopy(data)
        self.__data_id = data_id

    def crawl_builder(self):
        excel = self.get_excel()
        # TODO 商品数据的组装改成真实的数据
        excel.add_data(self.value_to_erp(self.__data))
        return CrawlBuilder() \
            .set_url('{}{}#{}'.format(config.get('hupun', 'service_host'), self.PATH, self.__data_id)) \
            .set_upload_files_kv('file', ('file.xlsx', excel.execute())) \
            .set_task_id(uuid.uuid4()) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[1][0])) \
            .set_post_data_kv('name', '供应商信息.xls') \
            .set_post_data_kv('exec', 'importSupplier') \
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
                "errMsg": result_msg,  # 如果code为1，请将失败的具体原因返回
                "supplier_msg": {}
            }
        else:
            supplier_msg = self.get_supplier_msg(self.__data.get('name'))
            return_msg = {
                "code": 0,  # 0：成功 1：失败
                "errMsg": '',  # 如果code为1，请将失败的具体原因返回
                "supplier_msg": supplier_msg,
            }

            # 同步成功，更新 es 中的供应商数据
            self.crawl_handler_page(Supplier(True).set_priority(Supplier.CONST_PRIORITY_FIRST))

        # 发送mq消息
        self.send_call_back_msg(return_msg=return_msg)
        return {
            'msg': return_msg,
            'date': Date.now().format(),
            'data': self.__data,
            'response': response.content
        }

    def get_supplier_msg(self, name, retry=3):
        """
        获取
        :return:
        """
        try:
            result = SupplierResult().get_result()
            for _ in result:
                if _.get('unitName') == name:
                    return_dict = {
                        'unitUid': _.get('unitUid'),
                        'comUid': _.get('comUid'),
                        'comUidcomUid': _.get('unitCode'),
                        'unitName': _.get('unitName'),
                    }
                    return return_dict
        except Exception as e:
            processor_logger.error(e)
            if retry > 1:
                return self.get_supplier_msg(retry - 1)
        return "未获取到供应商: {} 的信息".format(name)

    def value_to_erp(self, data):
        """
        把数据转为erp上传的对应字段
        :param data:
        :return:
        """
        the_list = {
            'supplier_name': data.get('name', ''),
        }
        return the_list

    def get_excel(self):
        """
        定义表头及字段名
        :return:
        """
        return Excel() \
            .add_header('NONE', '供应商编码') \
            .add_header('supplier_name', '<必填>供应商名称') \
            .add_header('NONE', '网站网址') \
            .add_header('NONE', '当前应付款') \
            .add_header('NONE', '省份') \
            .add_header('NONE', '市(区)') \
            .add_header('NONE', '区(县)') \
            .add_header('NONE', '地址') \
            .add_header('NONE', '邮编') \
            .add_header('NONE', '联系人') \
            .add_header('NONE', '固话') \
            .add_header('phone', '手机') \
            .add_header('NONE', 'E-mail') \
            .add_header('NONE', '税号') \
            .add_header('NONE', '传真') \
            .add_header('NONE', '开户行及账号') \
            .add_header('NONE', '业务员') \
            .add_header('NONE', '备注')

    def send_call_back_msg(self, return_msg={}):
        # 发送失败的消息
        if int(return_msg.get("code", 0)) != 0 and Helper.in_project_env():
            # 发送失败的消息
            title = '万里牛供应商同步(添加)操作失败'
            ding_msg = '万里牛供应商同步(添加)操作失败详情: {}'.format(return_msg.get("errMsg"))

            self.crawl_handler_page(DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg))
            # 同时发送邮件通知
            if self.__data.get('email'):
                EmailSender() \
                    .set_receiver(return_msg.get('email')) \
                    .set_mail_title(title) \
                    .set_mail_content(ding_msg) \
                    .send_email()

        from mq_handler import CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER_RESULT, CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        msg_tag = CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER_RESULT
        return_date = Date.now().format()
        MQ().publish_message(msg_tag, return_msg, self.__data_id, return_date, CONST_ACTION_UPDATE)
