import fire

from copy import deepcopy
from hupun_operator.model.es.inventory_sync import InventorySync
from pyspider.helper.date import Date


class Cron:
    def inventory_sync_del(self):
        """
        每12h删除一遍库存同步数据的失败部分
        :return:
        """
        print('开始删除存同步数据的失败部分,{}'.format(Date.now().format()))
        all_spu = InventorySync().get_all_spu_barcode()
        sync_time = Date.now().format_es_utc_with_tz()
        for spu in all_spu:
            print('本次删除数量:{}'.format(len(spu)))
            sended_data = []
            for _spu in spu:
                copy_data = deepcopy(_spu)
                copy_data['syncTime'] = sync_time
                copy_data['syncStatus'] = 0
                copy_data['failReason'] = ''
                sended_data.append(copy_data)
            InventorySync().update(sended_data, async=True)
        print('删除存同步数据的失败部分完成,{}'.format(Date.now().format()))


if __name__ == '__main__':
    fire.Fire(Cron)
