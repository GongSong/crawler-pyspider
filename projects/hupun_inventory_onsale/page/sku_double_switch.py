from hupun.page.base import *


class SkuDoubleSwitch(Base):
    """
    库存订单同步例外宝贝设置中，更改自动上架开关的状态
    """

    request_data = """
        <batch>
<request type="json"><![CDATA[
{"action":"resolve-data","dataResolver":"matchInterceptor#updateUploadPolicy","dataItems":[{"alias":"dsItem","data":{"$isWrapper":true,"$dataType":"v:inventory.item$[dtItem]","data":[
{"itemID":"%s","skuID":"%s","title":"黑色,S","status":0,"outerID":"19300D0005W106","properties":null,"modified":null,"pic1":null,"pic2":null,"pic3":null,"pic4":null,"pic5":null,"price":0,"url":null,
"upload":%d,"uploadable":false,"autoShelf":false,"companyID":"D1E338D6015630E3AFF2440F3CBBAFAD","shopID":"%s","shopNick":null,"shopType":0,"hasChild":false,"isItem":0,"virtualRatio":0,"expPolicy":{"$isWrapper":true,"$dataType":"v:inventory.item$[dtExpPolicy]","data":[]},"$dataType":"v:inventory.item$dtItem","$state":2,"$entityId":"25306"}]},"$dataType":"v:inventory.item$dtItem","$entityId":"25184"}]},"refreshMode":"value","autoResetEntityState":true}],"context":{}}
]]></request>
</batch>
        """

    def __init__(self, item_id, out_sku, target_status, shop_uid):
        # target_status为0时，关闭【上传库存】。为1时，开启【上传库存】。
        super(SkuDoubleSwitch, self).__init__()
        self.__item_id = item_id
        self.__target_status = target_status
        self.__shop_uid = shop_uid
        self.__out_sku = out_sku

    def get_request_data(self):
        return self.request_data % (self.__item_id, self.__out_sku, self.__target_status, self.__shop_uid)

    def get_unique_define(self):
        return merge_str('inventory_sync_upload', self.__item_id, self.__target_status)

    def parse_response(self, response, task):
        result = self.detect_xml_text(response.text)
        print('{}: 单次erp同步状态成功'.format(self.__item_id))


if __name__ == '__main__':
    SkuDoubleSwitch('TB586357341085', 'TB4413989658228', 0, 'D991C1F60CD5393F8DB19EADE17236F0').get_result()
