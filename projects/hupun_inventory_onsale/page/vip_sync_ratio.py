from hupun.page.base import *


class VipSyncRatio(Base):
    """
    库存订单同步例外宝贝设置中，更改自动上架开关的状态
    """

    request_data = """
        <batch>
<request type="json"><![CDATA[{"action":"resolve-data","dataResolver":"matchInterceptor#updateUploadPolicy","dataItems":[{"alias":"dsItem","data":{"$isWrapper":true,"$dataType":"v:inventory.item$[dtItem]","data":[
{"itemID":"%s",
"skuID":null,"title":"2019新款街头感撞色饰边牛仔裙","status":1,
"outerID":"1919Q00124B604","properties":"","modified":"1970-01-19T12:44:17Z","pic1":null,"pic2":null,"pic3":null,"pic4":null,"pic5":null,"price":0,"url":"","upload":%d,"uploadable":false,"autoShelf":false,"companyID":"D1E338D6015630E3AFF2440F3CBBAFAD","shopID":"C9ACE29003EC3B9BB24D01FCFBBF6BE7","shopNick":null,"shopType":0,"hasChild":false,"isItem":1,"virtualRatio":0,"expPolicy":
{"$isWrapper":true,"$dataType":"v:inventory.item$[dtExpPolicy]","data":[
{"com_uid":"D1E338D6015630E3AFF2440F3CBBAFAD","oln_item_id":"%s","oln_sku_id":"","oln_upload":%d,"shop_uid":"%s","storage_uid":"%s","quantity_type":%s,"upload_ratio":%s,"upload_beyond":%s,"shop_type":null,"sub_type":null,"shop_nick":null,"shop_name":null,"storage_name":"研发测试仓","$dataType":"v:inventory.item$dtExpPolicy","$state":2,"$entityId":"4092"}]},"$dataType":"v:inventory.item$dtItem","$entityId":"4037"}]},"refreshMode":"value","autoResetEntityState":true}],"context":{}}]]></request>

</batch>
        """

    def __init__(self, item_id, target_status, shop_uid='', quantity_type='null', upload_ratio='null',
                 storeage_uid='D1E338D6015630E3AFF2440F3CBBAFAD', virtual_inventory='0'):
        # target_status为1时，关闭【自动上架】。为2时，开启【自动上架】。
        super(VipSyncRatio, self).__init__()
        self.__item_id = item_id
        self.__target_status = target_status
        self.__upload_ratio = upload_ratio
        self.__quantity_type = quantity_type
        self.__shop_uid = shop_uid
        self.__storeage_uid = storeage_uid
        self.__virtual_inventory = virtual_inventory

    def get_request_data(self):
        return self.request_data % (self.__item_id, self.__target_status, self.__item_id, self.__target_status, self.__shop_uid,
                                    self.__storeage_uid, self.__quantity_type, self.__upload_ratio, self.__virtual_inventory)

    def get_unique_define(self):
        return merge_str('inventory_sync_upload', self.__item_id, self.__target_status)

    def parse_response(self, response, task):
        result = self.detect_xml_text(response.text)
        print('{}: 单次erp同步状态成功'.format(self.__item_id))


if __name__ == '__main__':
    # 库存比例
    VipSyncRatio('JI28526|30006275|VIPCNLGC01|1919Q00124B604', 2, 'C9ACE29003EC3B9BB24D01FCFBBF6BE7', '3', '50','D1E338D6015630E3AFF2440F3CBBAFAD','1').get_result()
