import os

from aliyun.log import LogClient
from pyspider.config import config

"""
阿里云的日志sdk
pip install -U aliyun-log-python-sdk
"""


class Sls:
    CONST_TALENT_PATH = 'crawler/table/talent/'
    CONST_SYCM_PATH = 'crawler/table/'
    CONST_JD_FLOW_PATH = 'crawler/table/flow/京东/'  # 京东流量数据
    CONST_JD_GOODS_PATH = 'crawler/table/京东/'  # 京东商品明细
    CONST_SYCM_FLOW_PATH = 'crawler/table/flow/生意参谋/'  # 生意参谋的流量来源数据文件下载

    def __init__(self, access_key_id, access_key_secret, endpoint):
        self.__access_key_id = access_key_id  # 阿里云访问密钥AccessKey ID。更多信息，请参见访问密钥。阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维。
        self.__access_key_secret = access_key_secret  # 阿里云访问密钥AccessKey Secret。
        self.__endpoint = endpoint  # 日志服务的域名。更多信息，请参见服务入口。此处以杭州为例，其它地域请根据实际情况填写。
        self.__client = LogClient(self.__endpoint, self.__access_key_id, self.__access_key_secret)  # 创建LogClient。

    def get_log_all(self, project, logstore, from_time, to_time):
        """
        获取所有的日志

        :type project: string
        :param project: project name

        :type logstore: string
        :param logstore: logstore name

        :type from_time: int/string
        :param from_time: the begin timestamp or format of time in readable time like "%Y-%m-%d %H:%M:%S<time_zone>" e.g. "2018-01-02 12:12:10+8:00", also support human readable string, e.g. "1 hour ago", "now", "yesterday 0:0:0", refer to https://aliyun-log-cli.readthedocs.io/en/latest/tutorials/tutorial_human_readable_datetime.html

        :type to_time: int/string
        :param to_time: the end timestamp or format of time in readable time like "%Y-%m-%d %H:%M:%S<time_zone>" e.g. "2018-01-02 12:12:10+8:00", also support human readable string, e.g. "1 hour ago", "now", "yesterday 0:0:0", refer to https://aliyun-log-cli.readthedocs.io/en/latest/tutorials/tutorial_human_readable_datetime.html

        """
        return self.__client.get_log_all(project, logstore, from_time, to_time)

    @staticmethod
    def get_key(path, *paths):
        return os.path.join(path, *paths)


sls = Sls(config.get('sls', 'access_key_id'),
          config.get('sls', 'access_key_secret'),
          config.get('sls', 'endpoint'))
