import datetime
import json


class CrawlBuilder:
    """
    为pyspider的handler类里面的crawl方法提供生成器
    """

    def __init__(self, url=''):
        """
        :param url:
        """
        self.__url = url
        self.__kwargs = {'age': 1, 'etag': False, 'last_modified': False}

    def set_url(self, url):
        """
        设置url
        :param url:
        :return:
        """
        self.__url = url
        return self

    def set_post_data_kv(self, key, value):
        """
        设置post的某个kv
        :param key:
        :param value:
        :return:
        """
        return self.update_kwargs_kv('data', {key: value})

    def set_post_data(self, data):
        """
        设置post的整个数据
        :param data:
        :return:
        """
        return self.set_kwargs_kv('data', data)

    def set_get_params_kv(self, key, value):
        """
        设置url里面的单个GET参数
        :param key:
        :param value:
        :return:
        """
        return self.update_kwargs_kv('params', {key: value})

    def set_get_params(self, params):
        """
        设置url里面的整个GET参数
        :param params:
        :return:
        """
        return self.set_kwargs_kv('params', params)

    def set_method(self, method='GET'):
        """
        设置请求是post还是get
        :param method:
        :return:
        """
        return self.set_kwargs_kv('method', method)

    def set_task_id(self, task_id):
        """
        自定义task id(要自己保证同一个抓取的全局唯一性)
        :param task_id:
        :return:
        """
        return self.set_kwargs_kv('taskid', task_id)

    def set_cookies(self, cookies: str):
        """
        设置cookies 字符串类型
        :param cookies:
        :return:
        """
        return self.update_kwargs_kv('headers', {'Cookie': cookies})

    def set_cookies_dict(self, cookies: dict):
        """
        设置cookies 字典类型
        :param cookies:
        :return:
        """
        return self.set_kwargs_kv('cookies', cookies)

    def set_proxy(self, proxy: str):
        """
        设置代理
        :param proxy:
        :return:
        """
        return self.set_kwargs_kv('proxy', proxy)

    def set_user_agent(self, user_agent: str):
        """
        设置user_agent
        :param user_agent:
        :return:
        """
        return self.set_kwargs_kv('user_agent', user_agent)

    def set_headers_kv(self, key, value: str):
        """
        设置某个header
        :param key:
        :param value:
        :return:
        """
        return self.update_kwargs_kv('headers', {key: value})

    def set_headers(self, headers: dict):
        """
        设置整个headers
        :param headers: dict
        :return:
        """
        return self.set_kwargs_kv('headers', headers)

    def set_upload_files_kv(self, key, path: str):
        """
        设置某个上传文件
        :param key:
        :param path:
        :return:
        """
        return self.update_kwargs_kv('files', {key: path})

    def set_upload_files(self, files: dict):
        """
        设置全部上传的文件
        :param files:
        :return:
        """
        return self.set_kwargs_kv('files', files)

    def set_save_kv(self, key, value):
        """
        设置post的某个kv
        :param key:
        :param value:
        :return:
        """
        return self.update_kwargs_kv('save', {key: value})

    def set_save(self, data: dict):
        """
        设置post的整个数据
        :param data:
        :return:
        """
        return self.set_kwargs_kv('save', data)

    def set_timeout(self, timeout):
        """
        设置请求的超时时间
        :param timeout:
        :return:
        """
        return self.set_kwargs_kv('timeout', timeout)

    def set_connect_timeout(self, conn_timeout):
        """
        设置请求的连接时间
        :param conn_timeout:
        :return:
        """
        return self.set_kwargs_kv('connect_timeout', conn_timeout)

    def set_fetch_type(self, fetch_type='js'):
        """
        设置 phantomjs 请求
        :param fetch_type:
        :return:
        """
        return self.set_kwargs_kv('fetch_type', fetch_type)

    def set_js_script(self, js_script):
        """
        设置 js 代码
        :param js_script:
        :return:
        """
        return self.set_kwargs_kv('js_script', js_script)

    def load_images(self, loaded):
        """
        设置 phantomjs 是否载入图片，false 为默认不载入
        :param loaded:
        :return:
        """
        return self.set_kwargs_kv('load_images', loaded)

    def set_min_wait_time(self, time=1):
        """
        执行 phantomjs 的 js 脚本的最小等待时间
        :param time:
        :return:
        """
        return self.set_kwargs_kv('min_wait_time', time)

    def schedule_priority(self, priority):
        """
        优先级数字越大排在越前面
        :param priority:
        :return:
        """
        return self.set_kwargs_kv('priority', priority)

    def schedule_retries(self, retries=3):
        """
        失败重试次数
        :param retries:
        :return:
        """
        return self.set_kwargs_kv('retries', retries)

    def schedule_exetime(self, exetime):
        """
        执行时间
        :param exetime:
        :return:
        """
        return self.set_kwargs_kv('exetime', exetime)

    def schedule_delay_second(self, second):
        """
        基于当前时间延迟多久执行
        :param second:
        :return:
        """
        return self.set_kwargs_kv('exetime', int(datetime.datetime.now().timestamp() + second))

    def schedule_age(self, age=1):
        """
        限制数据至少过多久才允许重新抓取,单位秒(设为1就是基本没有限制，想爬就爬)
        :param age:
        :return:
        """
        return self.set_kwargs_kv('age', age)

    def update_kwargs_kv(self, key, value):
        """
        更新某个参数键值对(解决参数的值如果是dict可以自动合并)
        :param key:
        :param value:
        :return:
        """
        if isinstance(value, dict) and isinstance(self.__kwargs.get(key), dict):
            self.__kwargs[key].update(value)
        else:
            self.__kwargs[key] = value
        return self

    def set_kwargs_kv(self, key, value):
        """
        设置Header的某个参数键值对
        :param key:
        :param value:
        :return:
        """
        self.__kwargs[key] = value
        return self

    def update_kwargs(self, kwargs: dict):
        """
        更新Header的整个参数键值对
        :param kwargs:
        :return:
        """
        for _key, _value in kwargs.items():
            self.update_kwargs_kv(_key, _value)
        return self

    def set_kwargs(self, kwargs):
        """
        更新整个参数键值对
        :param kwargs:
        :return:
        """
        self.__kwargs = kwargs
        return self

    def get_url(self):
        """
        获取url
        :return:
        """
        return self.__url

    def get_kwargs(self):
        """
        获取crawl方法的kwargs参数
        :return:
        """
        return self.__kwargs

    def get_proxy(self):
        return self.__kwargs.get('proxy')

    def get_cookies_dict(self):
        return self.__kwargs.get('cookies')

    def get_cookies_str(self):
        return self.__kwargs.get('headers', {}).get('Cookie')

    def set_post_json_data(self, data):
        """
        设置post请求，并且数据json化
        :param data:
        :return:
        """
        self.set_kwargs_kv('data', json.dumps(data))
        self.set_headers_kv('Content-Type', 'application/json ;charset=utf-8')
        return self
