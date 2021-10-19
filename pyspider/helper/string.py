import json
import re

regex = re.compile(r'\\(?![/u"])')


def merge_str(*args, dividing=':'):
    return dividing.join([str(_) for _ in args])


def format_str(value, default=''):
    if value:
        return str(value)
    return default


def json_loads(data, handle=False):
    """
    封装的json load
    :param data:
    :param handle: 补丁, False: 默认不特殊处理: True: 不走正则
    :return:
    """
    if handle:
        return json.loads(data.strip())
    return json.loads(regex.sub(r"\\\\", data.strip()))


def number_convert(number: str, convert_type='int', replace_char='%'):
    """
    接口数据里string类型的数转为数值类型
    :param number: string类型的数值
    :param convert_type: 转换的目标类型, eg: int, float
    :param replace_char: 需要替换string类型数值的特殊字符
    :return:
    """
    if convert_type == 'int':
        return int(number.replace(replace_char, ''))
    elif convert_type == 'float':
        if '%' in number:
            return float(number.replace('%', '').replace(replace_char, '')) / 100
        else:
            return float(number.replace(replace_char, ''))
    else:
        # 转换类型不符, 直接返回原数据
        return number
