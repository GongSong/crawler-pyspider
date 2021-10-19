import json
import os
import redis
from pyspider.config import config
from abc import ABC, abstractmethod
from pyspider.helper.date import get_now_timestamp_str
from enum import Enum, auto


class DataType(Enum):
    TEXT = auto()
    JSON = auto()
    BYTES = auto()


class StorageBase(ABC):
    @abstractmethod
    def set(self, key, value, ex=None):
        pass

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def exists(self, key):
        pass

    @abstractmethod
    def delete(self, key):
        pass


class StorageFile(StorageBase):
    def __init__(self, data_dir=None):
        if data_dir:
            self.__data_dir = data_dir
        else:
            self.__data_dir = config.get('app', 'data_dir')

    def get_full_path(self, key):
        return os.path.join(self.__data_dir, key)

    def set(self, key, value, ex=None):
        open(self.get_full_path(key), 'w+b' if isinstance(value, bytes) else 'w').write(value)

    def get(self, key, binary=False):
        if os.path.isfile(self.get_full_path(key)):
            return open(self.get_full_path(key), 'r+b' if binary else 'r').read()
        return False

    def exists(self, key):
        return os.path.isfile(self.get_full_path(key))

    def delete(self, key):
        if os.path.isfile(self.get_full_path(key)):
            os.rmdir(self.get_full_path(key))


class StorageRedis(StorageBase):
    def __init__(self, host=None, port=None, db=None):
        if host is None:
            host = config.get('redis', 'host')
        if port is None:
            port = config.get('redis', 'port')
        if db is None:
            db = config.get('redis', 'db')
        self.__client = redis.StrictRedis(host=host, port=port, db=db)

    def set(self, key, value, ex=None):
        self.__client.set(key, value, ex)

    def get(self, key, binary=False):
        data = self.__client.get(key)
        if binary:
            return data
        return data if not data else data.decode('utf8')

    def exists(self, key):
        return self.__client.exists(key)

    def delete(self, key):
        self.__client.delete(key)

    def lrange(self, key, start, end):
        return self.__client.lrange(key, start, end)

    def hset(self, key, memeber, value):
        return self.__client.hset(key, memeber, value)

    def hget(self, key, memeber):
        return self.__client.hget(key, memeber)

    def hgetall(self, key):
        return self.__client.hgetall(key)

    def sadd(self, key, value):
        return self.__client.sadd(key, value)

    def srandmember(self, key, number=None):
        return self.__client.srandmember(key, number)

    def srem(self, key, value):
        return self.__client.srem(key, value)

    def smembers(self, key):
        return self.__client.smembers(key)

    def lock(self, key, ex=3600):
        return self.__client.set(key, 1, ex=ex, nx=True)

    def type(self, key):
        return self.__client.type(key).decode()

    def keys(self, pattern='*'):
        return self.__client.keys(pattern)

    def incrby(self, name, amount=1):
        """
        Increments the value of key by amount. If no key exists, the value will be initialized as amount
        :param name:
        :param amount:
        :return:
        """
        return self.__client.incrby(name, amount)

    def ttl(self, name):
        return self.__client.ttl(name)

    def incr(self, key, amount=1):
        return self.__client.incr(key, amount)


class StorageData:
    def __init__(self, cache_key, storage=None, data_type=DataType.JSON):
        self.__data_type = data_type
        self.__storage = storage if storage else default_storage_file
        self.__cache_key = cache_key
        self.__data = None

    @property
    def data(self):
        if self.__data is None:
            data = self.__storage.get(self.__cache_key, self.__data_type == DataType.BYTES)
            if self.__data_type == DataType.JSON:
                data = json.loads(data) if data else {}
            self.__data = data
        return self.__data

    def get_full_path(self):
        if isinstance(self.__storage, StorageFile):
            return self.__storage.get_full_path(self.__cache_key)
        raise Exception('not file storage')

    def save(self):
        self.__storage.set(self.__cache_key, json.dumps(self.data) if self.__data_type == DataType.JSON else self.data)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def setdefault(self, key, value):
        return self.data.setdefault(key, value)

    def set(self, key, value):
        self.data[key] = value
        return value

    def exists(self, key):
        return key in self.data

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.__data = data

    def clear(self):
        self.__data = {} if self.__data_type == DataType.JSON else ''
        return self


class StorageDataRemoteSeparation:
    """
    local and remote data separation
    """

    def __init__(self, cache_key, storage_local=None, storage_remote=None, cache_key_update_time=None, data_type=DataType.JSON):
        # storage source
        self.__data_type = data_type
        self.__storage_local = storage_local if storage_local else default_storage_file
        self.__storage_remote = storage_remote if storage_remote else default_storage_redis

        # cache key
        self.__cache_key_remote = cache_key
        self.__cache_key_update_time = '_'.join([cache_key, 'update']) \
            if not cache_key_update_time else cache_key_update_time

        self.__new_update_time = None

        self.__data = None

    @property
    def data(self):
        if self.__data is None:
            self.__data = self.__get_local_data()
        return self.__data

    def set_new_update_time(self, new_update_time):
        self.__new_update_time = new_update_time
        return self

    def check_update_local_data(self, update_last_time=True, force=False):
        """
        check to update local data
        :return:
        """
        if not force and not self.is_need_update_local():
            return
        self.__data = self.__get_remote_data()
        self.__storage_local.set(self.__get_cache_key_local(), json.dumps(self.data) if self.__data_type == DataType.JSON else self.data)
        if update_last_time:
            self.save_update_time_local()

    def is_need_update_local(self):
        last_update_time_remote = self.__storage_remote.get(self.__cache_key_update_time)
        last_update_time_local = self.__storage_local.get(self.__cache_key_update_time)
        return not last_update_time_local or last_update_time_remote > last_update_time_local

    def update_to_remote(self, update_last_time=True):
        """
        update to remote
        :return:
        """
        self.__storage_remote.set(self.__cache_key_remote, json.dumps(self.data) if self.__data_type == DataType.JSON else self.data)
        if update_last_time:
            self.save_update_time_remote()

    def save_update_time_local(self):
        self.__storage_local.set(self.__cache_key_update_time, self.__new_update_time if self.__new_update_time else get_now_timestamp_str())

    def save_update_time_remote(self):
        self.__storage_remote.set(self.__cache_key_update_time, self.__new_update_time if self.__new_update_time else get_now_timestamp_str())

    def get_full_path(self):
        if isinstance(self.__storage_local, StorageFile):
            return self.__storage_local.get_full_path(self.__get_cache_key_local())
        raise Exception('not file storage')

    def get(self, key, default=None):
        return self.data.get(key, default)

    def setdefault(self, key, value):
        return self.data.setdefault(key, value)

    def set(self, key, value):
        self.data[key] = value
        return value

    def exists(self, key):
        return key in self.data

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.__data = data

    def clear(self):
        self.__data = {} if self.__data_type == DataType.JSON else ''
        return self

    def __get_local_data(self):
        """
        local data
        :return:
        """
        data = self.__storage_local.get(self.__get_cache_key_local(), self.__data_type == DataType.BYTES)
        if self.__data_type == DataType.JSON:
            data = json.loads(data) if data else {}
        return data

    def __get_remote_data(self):
        """
        remote data
        :return:
        """
        data = self.__storage_remote.get(self.__cache_key_remote, self.__data_type == DataType.BYTES)
        if self.__data_type == DataType.JSON:
            data = json.loads(data) if data else {}
        return data

    def __get_cache_key_local(self):
        """
        cache key with local update time
        :return:
        """
        return '_'.join([self.__cache_key_remote,
                         self.__new_update_time if self.__new_update_time else str(int(self.__storage_local.get(self.__cache_key_update_time)))])


default_storage_file = StorageFile()
default_storage_redis = StorageRedis()
ai_storage_redis = StorageRedis(
    config.get('redis', 'ai_host'),
    config.get('redis', 'ai_port'),
    config.get('redis', 'ai_db'))
