from hupun.page.base import *
import traceback


class CheckAllocateInventory(Base):
    """
    库存订单同步例外宝贝设置中，更改自动上架开关的状态
    """

    request_data = """
        <batch>
<request type="json"><![CDATA[{
"action":"resolve-data","dataResolver":"inventoryInterceptor#approveTransfer","dataItems":[{
"alias":"dsBill","data":{"$isWrapper":true,"$dataType":"v:inventory.transferNew$[dtTransferBill]","data":[{
"inv_change_uid":"%s","com_uid":"D1E338D6015630E3AFF2440F3CBBAFAD",
"storage_uid":"D1E338D6015630E3AFF2440F3CBBAFAD",
"storage_uid_tgt":"FBA807A72474376E8CFBBE9848F271B2",
"inv_change_code":"DB201912030003",
"bill_data":"2019-12-02T14:07:09Z",
"create_time":"2019-12-02T14:11:23Z",
"bill_type":4,"bill_sub_type":1,
"remark":"it测试用","bill_status":2,"oper_uid":"475571006758820808","approve_oper":null,"approve_time":null,
"storage_name":"总仓","storage_name_tgt":"研发测试仓","his":false,"oper_nick":"aipc1@yourdream.cc",
"approve_nick":null,"rowSelect":true,"pchsSum":1,"update_time":null,"storage_uid_jit":null,
"storage_name_jit":null,"arrival_time":null,"arrivalDate":null,"arrivalTime":null,"delivery_type":null,
"delivery_type_name":null,"delivery_uid":null,"delivery_code":null,"delivery_name":null,"jit_push_status":null,
"shop_nick":null,"diffNum":0,"diffMoney":0,"$dataType":"v:inventory.transferNew$dtTransferBill","$entityId":"3706"}]},
"refreshMode":"value","autoResetEntityState":true}],"parameter":{"remark":"it自动审核"},"context":{}}]]></request>
</batch>
        """

    def __init__(self, inv_change_uid):
        # target_status为1时，关闭【自动上架】。为2时，开启【自动上架】。
        super(CheckAllocateInventory, self).__init__()
        self.__inv_change_uid = inv_change_uid

    def get_request_data(self):
        return self.request_data % (self.__inv_change_uid)

    def get_unique_define(self):
        return merge_str('check_allocate_inventory', self.__inv_change_uid)

    def parse_response(self, response, task):
        print(response.text)
        try:
            if '会话过期' in response.text:
                return False, '会话过期'
            if '单据不存在' in response.text:
                return 'other', '单据不存在'
            elif '库存更新过于繁忙' in response.text:
                return 'rate', '库存更新过于繁忙'
            elif '单据已经被其他人操作' in response.text:
                return True, '单据已经被其他人操作'
            else:
                result = self.detect_xml_text(response.text)
                if result.get('entityStates', {}).get('3706', {}).get('bill_status') == 1:
                    print('{}: 单次erp同步状态成功'.format(self.__inv_change_uid))
                    return True, ''
                else:
                    return 'rate', '未被捕捉到的异常'
        except Exception as e:
            print(traceback.format_exc())
            return 'rate', '未被捕捉到的异常'


if __name__ == '__main__':
    # 根据cookie确定审核员的名字
    print(CheckAllocateInventory('DB201912030003').set_cookie_position(3).get_result())
