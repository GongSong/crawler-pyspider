import time
import traceback

from pyspider.config import config


class CrawlerHelper:
    """
    爬虫项目的工具类
    """

    @staticmethod
    def delay_by_task_count(task_obj, max_enqueue_num=200):
        """
        根据task数量缓慢写入抓取任务
        :param task_obj: 查询队列的task mongo实例
        :param max_enqueue_num: 写入队列的队列最大值
        :return:
        """
        # 检测当前抓取的队列数，数量过多则停止写入
        count = task_obj.find({'status': 1}).count()
        print('queue status:1 count: {}'.format(count))
        while count >= max_enqueue_num:
            time.sleep(int(count) / 6)
            count = task_obj.find({'status': 1}).count()

    @classmethod
    def get_sync_result(cls, obj, retry=3, delay_time=20):
        """
        通用的获取同步爬虫请求的方法
        :param obj: 同步爬虫的实例
        :param retry: 重试次数，默认重试3次
        :param delay_time: 延时时间
        :return:
        """
        try:
            print('获取爬虫: {} 的同步数据'.format(obj.__class__.__name__))
            result = obj.get_result()
            return 0, result
        except Exception as e:
            print('爬虫同步请求的error: {}'.format(e))
            print(traceback.format_exc())
            if retry > 0:
                time.sleep(delay_time)
                return cls.get_sync_result(obj, retry - 1)
            else:
                err = '爬虫: {} 同步获取数据重试次数剩余: {} 次,退出'.format(obj.__class__.__name__, retry)
                return 1, err

    @staticmethod
    def in_project_env():
        """
        判断目前的环境是否是正式环境
        :return:
        """
        product_env = 'product'
        env = config.get('app', 'env')
        if env == product_env:
            return True
        else:
            return False
