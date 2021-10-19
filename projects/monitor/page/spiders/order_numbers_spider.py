from hupun.page.base import *


class OrderNums(Base):
    request_data = '''
    <batch>
    <request type="json"><![CDATA[
    {
    "action":"load-data",
    "dataProvider":"saleInterceptor#queryTradeCount",
    "supportsEntity":true,
    "parameter":{
        "view":"sale.query",
        "dateType":1,
        "buyerType":"1",
        "exactType":1,
        "goodsType":1,
        "endDate":"%s",
        "startDate":"%s",
        "endTime":"%s",
        "history":false,
        "showModify":false,
        "refund":false,
        "detail":0,
        "containsPackage":false,
        "noSpecContainsPkg":false,
        "unRelated":false,
        "canMerge":false,
        "storage_uid":"D1E338D6015630E3AFF2440F3CBBAFAD,149273C58B8D312F8730DCE6EF8AB4EE,C29A34BEA7523A5BA04BF9E0A10040D0,61A1FD9EDABC3BE9A617EDF59D6E35CA,ABA16826CD14321ABA3FF3CAB7784D1D,80323619B8C739F2B697F9CFD34C34AC,84EC790FC3A23E949DA0405D3D3D67D8,FD98F002BB663577937C87F392F68BF9,1587DAF416163268975239F7EE04C500,B4E5BDD117F03E0F881CD6901713E7A4,1DE59E5DB146335DB473B7D261106184,21130C06EE723229AC379095BF0305A8,AF744068E6143BF987A27248B7657428,7819177595E23AAF959A1A25357A23F0,563D13C09F3634B097FDA859D696AC0E,723723F85D023DC5A5A02B8C83CA87A3,DE64474B8C073511958B97BAF70F9558,FBA807A72474376E8CFBBE9848F271B2,61071625A3CF3C3DB253ED30B3351DAB,","storage_name":"-- 所有仓库 --","salemanUid":"","saleman":"","startTime":null,"NOSIZE":"true"},"resultDataType":"v:sale.query$[Trade]","pageSize":"200","pageNo":1,"context":{},"loadedDataTypes":["dtCombination","Storage","Region","Oper","CombinationGoods","CustomAddress","dtQueryCondition","dtSearch","dtStorage","GoodsSpec","Order","operBillType","dtInvoice","dtMarkType","Country","dtSearchHistory","dtButtonDiy","Template","dtSide","MultiStorage","Trade","Combination","MultiOper","MultiShop","dtButton","PrintConfig","Shop","batchInventory","dtTradeAddition","dtBatch","dtSearchGoods","TradeLog","GoodsPermissions","CombinationDetail","dtGoodsUniqueCode","dtTradeStatement","dtJzPartner","dtMultiBarcode","dtSalePacking","dtSerialNumber","dtJzPartnerNew"]}]]></request>
    </batch>
    '''

    def __init__(self):
        super(OrderNums, self).__init__()

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, end_date)

    def get_unique_define(self):
        return merge_str('order_nums', self._start_time, self._end_time)

    def parse_response(self, response, task):
        result = self.detect_xml_text(response.text)
        # print(result['data']['entityCount'])
        return result['data']['entityCount']

    def get_erp_numbers(self):
        '''收集万里牛爬虫得到的数量'''
        erp_numbers = OrderNums() \
            .set_start_time(Date.now().plus_days(-0).to_day_start().format()) \
            .set_end_time(Date.now().plus_days(-0).to_day_end().format()) \
            .set_priority(OrderNums.CONST_PRIORITY_BUNDLED).get_result()
        return erp_numbers
