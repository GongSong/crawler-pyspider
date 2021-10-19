import os
from configparser import ConfigParser


class CustomConfigParser(ConfigParser):
    CONST_ENV_DEV = 'dev'
    CONST_ENV_TEST = 'test'
    CONST_ENV_PRODUCT = 'product'

    CONST_PROCESS_SCHEDULER = 'scheduler'
    CONST_PROCESS_FETCHER = 'fetcher'
    CONST_PROCESS_PROCESSOR = 'processor'
    CONST_PROCESS_RESULT = 'result'
    CONST_PROCESS_WEBUI = 'webui'
    CONST_PROCESS_PHANTOMJS = 'phantomjs'

    def __init__(self, *args, **kwargs):
        self.__process_name = 'unknow'
        super().__init__(*args, **kwargs)

    def is_product(self):
        return self.get('app', 'env') == 'product'

    def is_test(self):
        return self.get('app', 'env') == 'test'

    def is_dev(self):
        return self.get('app', 'env') == 'dev'

    def set_process_name(self, name):
        """
        设置进程名称
        :param name:
        :return:
        """
        self.__process_name = name

    def get_process_name(self):
        """
        获取进程名称
        :return:
        """
        return self.__process_name


os.environ['TZ'] = 'Asia/Shanghai'
config = CustomConfigParser()
config.read('conf/app.ini', 'utf-8')
