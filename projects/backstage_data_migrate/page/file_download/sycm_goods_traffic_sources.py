import time

from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.model.es.all_icy_goods import AllIcyGoods
from backstage_data_migrate.model.task import Task
from backstage_data_migrate.page.file_download.download_base import DownloadBase
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.date import Date
from backstage_data_migrate.config import *
from cookie.model.data import Data as CookieData
from pyspider.helper.utils import generator_list
from pyspider.libs.oss import oss


class SycmGoodsTraSources:
    """
    获取生意参谋每个商品的 商品流量来源 的相关方法
    """
    URL = 'https://sycm.taobao.com/flow/excel.do?_path_=v3/excel/item/source&belong=all&dateType={date_type}&' \
          'dateRange={start_date}|{end_date}&order=desc&orderBy=uv&device={device}&itemId={goods_id}'
    date_type = 'day'  # 抓取的日期类型
    device = 2  # 无线端
    file_suffix = 'xls'  # 用来判断的文件后缀
    file_warning_size = 10000  # 文件报警大小值
    max_enqueue_num = 300  # 写入队列的队列最大值
    list_size = 300  # 列表分片大小
    file_status_key = 'sycm_goods_traffic_sources'  # 标记本次文件下载是否正常下载到的标记
    file_key_expire_time = 60  # 本次正常下载标记的过期时间
    device_map = {
        0: 'pc端',
        2: '无线端',
    }

    def __init__(self, start_day, end_day, username, channel, delay_seconds=0):
        self.__start_date = Date.now().plus_days(-end_day).format(full=False)
        self.__end_date = Date.now().plus_days(-start_day).format(full=False)
        self.__username = username
        self.__channel = channel
        self.__day_date = self.__end_date
        self.__delay_seconds = delay_seconds

    def start(self):
        """
        启动入口
        :return:
        """
        goods_ids = AllIcyGoods().get_all_goods_id()
        for goods_id in goods_ids:
            goods_id_list = generator_list(goods_id, self.list_size)
            for _id_list in goods_id_list:
                # 延时逐渐写入抓取队列
                self.delay_by_task_count()
                for _id in _id_list:
                    tmall_goods_id = _id.get('tmallGoodsId')
                    url = self.URL.format(date_type=self.date_type, start_date=self.__start_date, end_date=self.__end_date,
                                          device=self.device, goods_id=tmall_goods_id)
                    DownloadBase(url) \
                        .set_cookies_config(CookieData.CONST_PLATFORM_TAOBAO_SYCM, self.__username) \
                        .set_file_size(self.file_warning_size) \
                        .set_table_type(self.file_suffix) \
                        .set_oss_path(self.get_file_path(tmall_goods_id)) \
                        .set_crawl_file_status(self.file_status_key, self.file_key_expire_time) \
                        .enqueue()

    @classmethod
    def check(cls):
        """
        检查本次数据抓取是否成功
        :return:
        """
        status = default_storage_redis.get(cls.file_status_key)
        print('检查本次数据抓取是否成功的状态: {}'.format(status))
        if not status:
            # 失败
            title = '生意参谋每个商品的流量来源抓取爬虫出现异常'
            text = '生意参谋的每个商品的流量来源抓取爬虫出现异常，请及时检查是否是因为cookie失效'
            DingTalk(ROBOT_TOKEN, title, text)
            print('error details: {}'.format(text))
        else:
            # 成功
            print('本次数据正常抓取')

    def delay_by_task_count(self):
        """
        根据task数量缓慢写入抓取任务
        :return:
        """
        # 检测当前抓取的队列数，数量过多则停止写入
        count = Task().find({'status': 1}).count()
        print('queue status:1 count: {}'.format(count))
        while count >= self.max_enqueue_num:
            time.sleep(int(count) / 6)
            count = Task().find({'status': 1}).count()

    def get_file_path(self, goods_id):
        """
        获取写入oss的路径
        :param goods_id: 商品ID
        :return:
        """
        file_name = '{channel}/goods_traffic_sources/{date_type}/{day_date}/[生意参谋商品流量来源][{device}][{goods_id}]{start_date}--{end_date}.xls'.format(
            channel=self.__channel,
            date_type=self.date_type,
            day_date=self.__day_date,
            device=self.device_map.get(self.device),
            goods_id=goods_id,
            start_date=self.__start_date,
            end_date=self.__end_date
        )
        file_path = oss.get_key(oss.CONST_SYCM_GOODS_TRAFFIC_SOURCES, file_name)
        return file_path
