from math import ceil
import functools
from pyspider.core.model.storage import ai_storage_redis


def generator_page(count, page_size, start=1):
    for page in range(start, int(ceil(count/page_size))+1):
        yield page


def generator_list(l, page_size, start=1):
    _list = list(l)
    for page in range(start, int(ceil(len(_list)/page_size)+1)):
        yield _list[(page-1)*page_size:page*page_size]


def division(a, b, multiple=100, default=0, ndigits=2):
    """
    除法计算
    :param double a:
    :param double b:
    :param double multiple:
    :param double default:
    :param ndigits:
    :return:
    """
    return round(a / b * multiple, ndigits) if b > 0 else default


def number_to_any_str(n, s='0123'):
    base = len(s)
    if n < base:
        return s[n]
    else:
        return number_to_any_str(n // base, s) + s[n % base]


def random_copy(s):
    s1 = s
    s2 = s[::-1]
    result = ''
    for _index, _value in enumerate(s1):
        result += _value * int(s2[_index])
    return result


def deep_format_float(data):
    if type(data) == list:
        data = [deep_format_float(_) for _ in data]
    elif type(data) == dict:
        data = dict([(k, deep_format_float(v)) for k, v in data.items()])
    return format_float(data)


def format_float(value):
    if type(value) not in [int, float]:
        return value
    return round(value, 2)


def progress_counter(key='', step=1):
    """
    用于进度记录
    :param key:
    :param step:
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            func(*args, **kw)
            ai_storage_redis.incrby(key, step)

        return wrapper

    return decorator


def get_tunnel_proxy():
    """
    获取隧道代理
    :return:
    """
    # 代理服务器
    proxy_host = "http-dyn.abuyun.com"
    proxy_port = "9020"

    # 代理隧道验证信息
    proxy_user = "H91903506A95A37D"
    proxy_pass = "77A04EC4C610C967"

    return "http://{user}:{pwd}@[{host}]:{port}".format(user=proxy_user, pwd=proxy_pass, host=proxy_host,
                                                        port=proxy_port)
