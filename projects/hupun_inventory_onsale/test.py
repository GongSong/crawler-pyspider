import gevent.monkey
gevent.monkey.patch_ssl()
import unittest
# from hupun_inventory_onsale.change_inventory_status import ChangeInventoryStatus
from hupun_inventory_onsale.page.inventory_sync_upload import InventorySyncUpload
from hupun_inventory_onsale.page.inverntory_sync_config import InventorySyncConfig
from hupun_inventory_onsale.page.weipinhui_query_shelf_status import VipQueryShelfStatus


class Test(unittest.TestCase):
    def _test_inventory_sync_config(self):
        """
        查看库存同步例外宝贝的商品状态 的测试部分
        :return:
        """
        # InventorySyncConfig('19300D0005', 'D991C1F60CD5393F8DB19EADE17236F0').test()
        a = InventorySyncConfig('', 'C9ACE29003EC3B9BB24D01FCFBBF6BE7').set_cookie_position(1).get_result()
        # a = InventorySyncConfig('日常', '9A1C9BFF3C67302393D9BE60BB53B8EE').get_result(retry_limit=2)
        print(a)

    def _test_inventory_sync_upload(self):
        """
        更改库存同步例外宝贝的【自动上架】 的测试部分
        :return:
        """
        # InventorySyncUpload('19300D0005', 'D991C1F60CD5393F8DB19EADE17236F0').test()
        InventorySyncUpload('HS5924face46283904c69375e6', 1).set_cookie_position(1).test()

    def _test_change_invenroty_status(self):
        '''
        更改【自动上架】完整操作 的测试部分
        :return:
        '''
        # ChangeInventoryStatus('19300D0005', 'D991C1F60CD5393F8DB19EADE17236F0', 2).change_erp_status()
        # ChangeInventoryStatus().change_erp_status()
        pass

    def test_query_shelf_status(self):
        res = VipQueryShelfStatus()
        print('++++++++')
        print(res)