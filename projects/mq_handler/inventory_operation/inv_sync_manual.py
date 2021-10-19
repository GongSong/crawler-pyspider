import traceback

from alarm.page.ding_talk import DingTalk
from hupun_operator.page.inventory.inventory_sync_common import InvSyncCommon
from mq_handler.base import Base
from pyspider.core.model.storage import default_storage_redis, ai_storage_redis
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.date import Date


class InvSyncManual(Base):
    """
    手动更新各渠道库存
    isAll为1时全量更新 0是部分更新
    """
    ROBOT_TOKEN = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
    # 重置状态，用于库存配置更改后的商品从头开始上传
    goods_upload_status = 'goodsUploadStatus'
    # 进度完成的redis key
    PROGRESS_FINISHED = 'sync_finished'
    # 进度程度的redis key
    PROGRESS_RUNNING = 'inv_sync'
    # 默认的redis key所属类别为spu
    DEFAULT_KEY_TYPE = 'spu'

    def execute(self):
        print('手动更新各渠道库存')
        self.print_basic_info()
        # 写入数据
        self.handle_data()

    def handle_data(self):
        """
        处理数据区
        :return:
        """
        try:
            print('开始手动更新各渠道库存')

            is_all = int(self._data['isAll'])
            # 传入的 spu 可能是sku，也可能是spu，具体是由flag字段决定它是哪个
            spus = self._data.get('spu')
            is_all = True if is_all else False
            flag = self._data.get('flag')
            if flag not in ['sku', 'spu']:
                raise Exception('传入的flag:{}不符合要求,需要传入字段sku或者spu'.format(flag))
            self.DEFAULT_KEY_TYPE = flag

            print('设置本次上传库存的redis同步状态为0(进行中)')
            # 初始化进度状态的值
            ai_storage_redis.set(':'.join([self.PROGRESS_FINISHED, self.DEFAULT_KEY_TYPE]), 0)
            # 初始化进度的值
            ai_storage_redis.set(':'.join([self.PROGRESS_RUNNING, self.DEFAULT_KEY_TYPE]), 0)

            # 更改商品的同步状态
            inv_obj = InvSyncCommon()
            inv_obj.set_goods_pending(spus, is_all)

            status_timestamp = Date.now().timestamp()
            default_storage_redis.set(self.goods_upload_status, status_timestamp)
            inv_obj \
                .set_sync_flag(flag) \
                .sync_inventory_goods(spus, is_all, status_timestamp)
        except Exception as e:
            err_msg = "手动更新各渠道库存出现知错误:{}".format(e)
            print('err_msg', err_msg)
            print(traceback.format_exc())
            # 添加报警通知
            if CrawlerHelper.in_project_env():
                title = '手动更新各渠道库存发生未知异常'
                ding_msg = err_msg
                DingTalk(self.ROBOT_TOKEN, title, ding_msg).enqueue()
        finally:
            print('设置本次上传库存的redis同步状态为1(完成)')
            ai_storage_redis.set(':'.join([self.PROGRESS_FINISHED, self.DEFAULT_KEY_TYPE]), 1)
