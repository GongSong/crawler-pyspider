from pyspider.helper.excel_reader import ExcelReader
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData


class DownloadExcelDetect(BaseCrawl):
    """
    上传商品数据到erp
    """
    PATH = '/excel.do'

    def __init__(self, k):
        """
        下载excel文件, 以json的方式返回
        :param k:
        """
        super(BaseCrawl, self).__init__()
        self.k = k

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url('{}{}'.format(config.get('hupun', 'service_host'), self.PATH)) \
            .set_task_id('test') \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[0][0])) \
            .set_get_params_kv('k', self.k)

    def parse_response(self, response, task):
        try:
            result = ExcelReader(file_contents=response.content) \
                .add_header('sku', '商品编码') \
                .add_header('NONE', '商品条码') \
                .add_header('NONE', '商品名称') \
                .add_header('NONE', '规格名称') \
                .add_header('count', '<必填>采购数量') \
                .add_header('price', '<必填>单价') \
                .add_header('NONE', '折扣率(%)') \
                .add_header('cycle', '采购周期') \
                .add_header('arrivalDate', '到货日期') \
                .add_header('NONE', '商品备注') \
                .add_header('supplier', '供应商') \
                .add_header('salesman', '业务员账号') \
                .add_header('NONE', '结算方式') \
                .add_header('error', '错误内容') \
                .get_result()
            return result
        except Exception as e:
            print('写入error数据到Excel失败: {}'.format(e))
            return [{'error': '写入error数据到Excel失败'}]
