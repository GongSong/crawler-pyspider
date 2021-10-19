import time

from alarm.page.ding_talk import DingTalk
from pyspider.config import config


class Helper:
    """
    爬虫项目的工具类
    """

    @staticmethod
    def send_to_ding_talk(token, title, content):
        DingTalk(token, title, content).enqueue()

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

    @classmethod
    def get_sync_result(cls, obj, retry=3, delay_time=25, proxy=None):
        """
        通用的获取同步爬虫请求的方法
        :param obj: 同步爬虫的实例
        :param retry: 重试次数，默认重试3次
        :param delay_time: 重试延迟时间
        :param proxy: IP代理
        :return:
        """
        try:
            print('获取爬虫: {} 的同步数据'.format(obj.__class__.__name__))
            if proxy and retry < 2:
                result = obj.set_proxy(proxy).get_result()
            else:
                result = obj.get_result()
            return 0, result
        except Exception as e:
            err_msg = '爬虫同步请求的error: {}'.format(e)
            print(err_msg)
            if retry > 0:
                time.sleep(delay_time)
                return cls.get_sync_result(obj, retry=retry - 1, delay_time=delay_time, proxy=proxy)
            else:
                err = '爬虫: {} 同步获取数据重试次数剩余: {} 次,退出, error_msg: {}'.format(obj.__class__.__name__, retry, err_msg)
                return 1, err
