import redis

from pyspider.helper.logging import processor_logger
from backstage_data_migrate.config import *


def save_to_redis(name, response):
    if len(response.content) > 3000 and response.status_code == 200:
        my_redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_ID)
        empty_redis(my_redis, name)
        my_redis.rpush(name, response.content)
        processor_logger.info('写入{}完成'.format(name))
        processor_logger.info('获取到了流量来源{}的数据'.format(name))
    else:
        processor_logger.warning('获取流量来源{}的数据获取失败'.format(name))


def empty_redis(my_redis, name):
    """
    清空key对应的redis
    :param my_redis:
    :param name:
    :return:
    """
    while True:
        a = my_redis.lpop(name)
        if a is not None:
            processor_logger.warning('pop {}'.format(name))
            continue
        else:
            break
