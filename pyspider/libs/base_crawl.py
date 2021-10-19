import sys
import time

import abc
from pyspider.config import config
from pyspider.libs.base_handler import BaseHandler
from pyspider.libs.crawl_builder import CrawlBuilder
from pyspider.libs.oss import oss
from pyspider.helper.cookies_pool import CookiesPool
from pyspider.helper.logging import processor_logger, result_logger, task_monitor
from pyspider.libs.response import rebuild_response
from pyspider.libs.utils import md5string, unicode_obj, get_project_name
from pyspider.message_queue import connect_message_queue
from pyspider.fetcher import tornado_fetcher
from pyspider.core.model.storage import default_storage_redis


class BaseCrawl:
    CONST_STOP_PREFIX_KEY = 'crawl_stop_'
    CONST_FLAG_NONE = ''
    CONST_FLAG_BREAK = 'break'
    CONST_FLAG_CANCEL = 'cancel'
    CONST_FLAG_PAUSE = 'pause'

    def __init__(self):
        self._url = ''
        self.__follows = []
        self.__messages = []

    def send_message(self, msg, url):
        self.__messages.append({'msg': msg, 'url': url})
        return self

    def crawl_handler_page(self, handler_page):
        self.__follows.append(handler_page)
        return self

    def get_follows(self):
        return self.__follows

    def get_messages(self):
        return self.__messages

    @staticmethod
    def in_processor():
        return config.get_process_name() == config.CONST_PROCESS_PROCESSOR

    @classmethod
    def set_flag(cls, flag):
        """
        对某个page打全局标记
        :param flag:
        :return:
        """
        default_storage_redis.set(BaseCrawl.CONST_STOP_PREFIX_KEY+cls.__module__, flag)

    @classmethod
    def check_flag(cls, flag):
        """
        获取某个page的全局标记
        :return:
        """
        return cls.get_flag() == flag

    @classmethod
    def get_flag(cls):
        """
        获取某个page的全局标记
        :return:
        """
        return default_storage_redis.get(BaseCrawl.CONST_STOP_PREFIX_KEY+cls.__module__)

    @abc.abstractmethod
    def crawl_builder(self):
        """
        生成爬虫请求生成器
        processor和fetcher进程会调用
        :return: CrawlBuilder
        """
        pass

    @abc.abstractmethod
    def parse_response(self, response, task):
        """
        根据爬取结果进行分析处理, 这里可以调用send_message, crawl_handler_page分发新的抓取页面
        processor 进程调用
        :return:
        """
        pass

    def result_hook(self, result, task):
        """
        保存到数据库之后会执行的操作, 可以重载该方法作保存结果之后的特殊操作
        比如某些特殊回调地址需要等数据保存成功之后才能调用
        result 进程调用
        :return:
        """
        pass

    def enqueue(self):
        """
        直接入队，任何进程里面都可以直接调用
        :return:
        """
        handler = BaseHandler()
        handler._reset()
        handler.project_name = get_project_name(self)
        task = handler.crawl_handler_page(self)
        connect_message_queue('newtask_queue', config.get('message_queue', 'url')).put([unicode_obj(task)])

    def get_result(self, retry_limit=0, retry_interval=1):
        """
        测试抓取
        :return:
        """
        retries = 0
        while True:
            handler = BaseHandler()
            handler._reset()
            handler.project_name = get_project_name(self)
            task = handler.crawl_handler_page(self)
            try:
                start_time = time.time()
                response = rebuild_response(tornado_fetcher.Fetcher(None, None, async_mode=False).fetch(task))
                task.setdefault('track', {}).setdefault('fetch', {
                    'ok': response.isok(),
                    'redirect_url': response.url if response.url != response.orig_url else None,
                    'time': time.time() - start_time,
                    'error': response.error,
                    'status_code': response.status_code,
                    'encoding': getattr(response, '_encoding', None),
                    'content_len': len(response.content) if response.content else 0
                })
                start_time = time.time()
                result = self.parse_response(response, task)
                task.setdefault('track', {}).setdefault('process', {
                    'ok': True,
                    'time': time.time() - start_time,
                })
                task_monitor(task, 'success')
                return result
            except Exception as e:
                if retry_limit <= retries:
                    task_monitor(task, 'failed')
                    raise e
                task_monitor(task, 'retry')
                retries += 1
                task.setdefault('schedule', {}).setdefault('retries', retries)
                time.sleep(retry_interval)

    def test(self, retry_limit=0, retry_interval=1):
        """
        测试抓取
        :return:
        """
        while True:
            try:
                handler = BaseHandler()
                handler._reset()
                handler.project_name = get_project_name(self)
                task = handler.crawl_handler_page(self)
                response = tornado_fetcher.Fetcher(None, None, async_mode=False).fetch(task)
                self.test_result(self.parse_response(rebuild_response(response), task))
                return True
            except Exception as e:
                if retry_limit <= 0:
                    raise e
                retry_limit -= 1
                time.sleep(retry_interval)

    def test_result(self, result):
        """
        对结果进行校验,需要对结果进行校验的页面重载该方法，如果数据有问题把异常抛出,跑单元测试的时候会检查异常
        :param result:
        :return:
        """
        pass
