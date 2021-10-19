from hupun.page.base import *

class AppointmentSkuInfo(Base):
    """
    查询 预约出库单内sku信息
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[
    {"action":"load-data","dataProvider":"goodsInterceptor#queryGoodsAndSpec","supportsEntity":true,"parameter":
    {"condition": "%s",
    "isSupplierOwn":"0","showPackage":null,
    "storageUid":"%s",
    "distr_uid":null,"ifexistPurchs":"ifexistPurchs"},"resultDataType":"v:inventory.outboundAppointment$[GoodsSpec]",
    "pageSize":10,"pageNo":1,"context":{},
    "loadedDataTypes":["dtFractUnit","Catagory","Template","appointmentDetail","Oper","GoodsSpec","Region","dtSearch","Combination","Storage","PrintConfig","inventoryInOutReason","appointmentBill","GoodsPermissions","CombinationDetail","DistrCompany"]}]]></request>

    </batch>
    """

    def __init__(self, sku, count=1, storage_uid="FBA807A72474376E8CFBBE9848F271B2"):
        super(AppointmentSkuInfo, self).__init__()
        self.__sku = sku
        self.__storage_uid = storage_uid
        self.__count = count

    def get_request_data(self):
        return self.request_data % (self.__sku, self.__storage_uid)

    def get_unique_define(self):
        return merge_str('appointment_sku_info', self.__sku, self.__storage_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        item_list = []
        if len(result['data']):
            for _item in result.get('data',{}).get("data"):
                # print(_item)
                spec_code = _item.get("specCode")
                if spec_code != self.__sku:
                    continue
                price = _item.get("primePrice", 0)
                good_uid = _item.get("goodsUid")
                goods_name = _item.get("goodsName")
                spec_uid = _item.get("specUid")
                spec_name = _item.get("specValue")
                sum = price * self.__count

                sku_info = {
                        "price":price,
                        "pchs_price":price,
                        "status":0,
                        "finish":False,
                        "s":True,
                        "unit_size":1,
                        "isPackage":False,
                        "goods_uid":good_uid,
                        "goods_name":goods_name,
                        "goodsRemark":None,
                        "spec_uid":spec_uid,
                        "spec_code":spec_code,
                        "spec_name":spec_name,
                        "size":self.__count,
                        "pchs_size":self.__count,
                        "sum":sum,
                        "unit":"件",
                        "unit_uid":None,
                        "pchs_unit":"件",
                        "ifexistPurchs":None,
                        "$dataType":"appointmentDetail",
                        "$state":1,
                        "$entityId":"1070"
                      }
                item_list.append(sku_info)
        print(item_list)
        return item_list[0]



if __name__ == '__main__':
    AppointmentSkuInfo("2020D00018W502", 1, "FBA807A72474376E8CFBBE9848F271B2").use_cookie_pool().get_result()




