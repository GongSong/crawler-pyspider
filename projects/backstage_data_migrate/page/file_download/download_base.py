from backstage_data_migrate.config import *
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData


class DownloadBase(BaseCrawl):
    """
    文件下载的公共爬虫，支持通用类型的文件下载和保存
    """

    def __init__(self, url):
        super(DownloadBase, self).__init__()
        self.__url = url
        self.__oss_path = ''
        self.__cookies = None
        self.__table_type = ''
        self.__priority = 0
        self.__file_size = 0
        self.__file_status_key = ''
        self.__file_expire_time = 3600
        self.__taobao_warning_words = ['亲，访问受限了']  # 如果有这些关键词，则代表没有正常获取到数据

    def set_cookies_config(self, platform, username):
        """
        手动设置cookies
        :param platform: cookie 的所属平台
        :param username: cookie 所属的用户名
        :return:
        """
        self.__cookies = CookieData.get(platform, username)
        return self

    def set_oss_path(self, path):
        """
        设置保存下载内容的oss路径
        :param path:
        :return:
        """
        self.__oss_path = path
        return self

    def set_table_type(self, table_type):
        """
        设置本次下载的表格的类型, 通常有：xml、sheet、xls
        :param table_type:
        :return:
        """
        self.__table_type = table_type
        return self

    def set_priority(self, priority):
        """
        设置本次下载的表格的抓取级别
        :param priority:
        :return:
        """
        self.__priority = priority
        return self

    def set_file_size(self, size):
        """
        设置判断正常获取到下载文件的大小预警值；
        比如，如果下载的文件大小为1000，预警值为2000，那么本次下载就是失败的
        :param size: 下载文件的大小预警值
        :return:
        """
        self.__file_size = size
        return self

    def set_crawl_file_status(self, status_key, expire_time=3600):
        """
        在redis中设置文件是否被正常抓取到的状态
        :param status_key: 文件类型的唯一标识
        :param expire_time: key 的过期时间, 默认为1小时
        :return:
        """
        self.__file_status_key = status_key
        self.__file_expire_time = expire_time
        return self

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(':'.join([self.__url, self.__oss_path])))
        if self.__cookies:
            builder.set_cookies(self.__cookies)
        if self.__priority:
            builder.schedule_priority(self.__priority)
        return builder

    def parse_response(self, response, task):
        # 判断是否正常拿到了数据, 没拿到，则结束本次爬虫抓取
        for words in self.__taobao_warning_words:
            if words in response.text:
                return {
                    'url': self.__url,
                    'excel_size': len(response.content),
                    'saved_oss_path': self.__oss_path,
                    'unique_name': 'download_file'
                }
        if len(response.content) < self.__file_size:
            processor_logger.error('cookie error')
            assert False, 'cookie 过期'
        if self.__table_type and 'Content-Disposition' in response.headers \
            and self.__table_type not in response.headers['Content-Disposition']:
            processor_logger.error('table type error')
            assert False, 'cookie 过期, table_type:{}, oss_path: {}'.format(self.__table_type, self.__oss_path)

        if self.__oss_path:
            # 保存到oss
            oss.upload_data(self.__oss_path, response.content)
        if self.__file_status_key:
            default_storage_redis.set(self.__file_status_key, 1, self.__file_expire_time)

        return {
            'url': self.__url,
            'excel_size': len(response.content),
            'saved_oss_path': self.__oss_path,
            'unique_name': 'download_file'
        }
