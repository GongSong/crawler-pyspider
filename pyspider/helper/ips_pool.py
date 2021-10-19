from random import choice
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.logging import logger


class IpRedis:
    def __init__(self):
        """
        保存IP的数据池
        """
        self.__redis = default_storage_redis

    def all(self):
        """
        获取全部代理
        :return:
        """
        ip_list = []
        keys = self.__redis.keys('ips:*')
        if keys:
            for _key in keys:
                ip_list.append(self.__redis.get(_key))
        return ip_list

    def add(self, proxy):
        """
        添加代理
        :param proxy: IP代理
        :return:
        """
        ip_key = 'ips:{}'.format(proxy)
        if not self.__redis.exists(ip_key):
            return self.__redis.set(ip_key, proxy)

    def delete(self, proxy):
        """
        删除代理
        :param proxy:
        :return:
        """
        ip_key = 'ips:{}'.format(proxy)
        return self.__redis.delete(ip_key)

    def exists(self, proxy):
        """
        判断是否存在
        :param proxy:
        :return:
        """
        ip_key = 'ips:{}'.format(proxy)
        return self.__redis.exists(ip_key)

    def count(self):
        """
        返回代理的数量
        :return:
        """
        pattern = 'ips:*'
        return len(self.__redis.keys(pattern))

    def random(self):
        """
        返回一个随机的代理;
        没有则返回空字符串
        :return:
        """
        result = self.all()
        if result:
            return choice(result)
        else:
            return ''


class IpsPool:

    @classmethod
    def get_ip_from_pool(cls):
        """
        从 IP 池获取 IP，没有 IP 则返回空 str
        :return:
        """
        proxy_ip = IpRedis().random()
        logger.info("获取了IP: {}".format(proxy_ip))
        return proxy_ip

    @classmethod
    def delete_ip(cls, ip):
        """
        从 IP 池删除失效 IP
        :param ip:
        :return:
        """
        result = IpRedis().delete(ip)
        if result:
            logger.info('删除ip: {}成功'.format(result))
            print('删除ip: {}成功'.format(ip))
        else:
            print('删除ip: {}失败'.format(ip))
