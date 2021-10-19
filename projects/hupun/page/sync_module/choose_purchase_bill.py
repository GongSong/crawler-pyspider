from hupun.page.base import *


class ChoosePurBill(Base):
    """
    根据单据编号、供应商和仓库等参数获取 采购入库单 的选择采购订单部分的采购订单详情
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"purchaseInterceptor#queryBill4StockIn",
   "supportsEntity":true,
   "parameter":{
     "days":null,
     "startDate":"%s",
     "endDate":"%s",
     "billType":0,
     "storageUid":"%s",
     "storageName":"%s",
     "supplierUid":"%s",
     "supplierName":"%s",
     "caption":"采购入库",
     "detail_uid":"",
     "billStatus":"1,2",
     "detailStatus":"0,1",
     "currencyCode":"",
     "billCode":"%s",
     "goods":null,
     "multiStatus":"1,2"
   },
   "resultDataType":"v:purchase.SelectPchsBill$[pchsBill]",
   "pageSize":10,
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
     "dtCondition",
     "pchsBill",
     "dtSearchGoods",
     "Storage"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, bill_code, storage_uid, storage_name, supplier_uid, supplier_name):
        super(ChoosePurBill, self).__init__()
        self.__bill_code = bill_code
        self.__storage_uid = storage_uid
        self.__storage_name = storage_name
        self.__supplier_uid = supplier_uid
        self.__supplier_name = supplier_name

    def get_request_data(self):
        start_date = Date(self._start_time).format_es_old_utc() if self._start_time else \
            Date.now().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self.__storage_uid, self.__storage_name,
                                    self.__supplier_uid, self.__supplier_name, self.__bill_code)

    def get_unique_define(self):
        return merge_str('choose_purchase_bill', self.__bill_code)

    def parse_response(self, response, task):
        # json 结果
        if 'MessageBox' in response.text:
            print('get ChoosePurBill result error details: {}'.format(response.text))
            err_msg = response.text.split('MessageBox')[-1] \
                .replace('ERROR_ICON', '').replace('message', '').replace('</exception>', '') \
                .replace('</request>', '').replace('</result>', '').replace(' ', '')
            raise Exception(err_msg)

        result = self.detect_xml_text(response.text)['data']['data']
        return result
