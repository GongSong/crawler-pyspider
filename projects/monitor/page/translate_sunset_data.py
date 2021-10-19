from monitor.model.es.monitor_save2 import MonitorSave2
from pyspider.helper.date import Date
import datetime

from pyspider.helper.es_query_builder import EsQueryBuilder, EsAggsBuilder


def normalizer_ctime(minute=5) -> Date:
    '''规整当前时间,每5分钟范围内的时间取整'''
    now_minute = datetime.datetime.now().minute
    now_minute_format = now_minute // minute * minute
    now_time_format = datetime.datetime.now().replace(minute=now_minute_format, second=0)
    normalizer_ctime = Date(now_time_format)
    return normalizer_ctime


# a_list = [{'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '采购爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '天猫爬虫',
#            'project_name': '采购商品爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '商品采购爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单采购爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '天猫爬虫',
#            'project_name': '采购商品爬虫',
#            'project_status': 0},
#           ]



normalized_insert_time = MonitorSave2().get_last_normalized_insert_time()
a = MonitorSave2().scroll(
                    EsQueryBuilder()
                    .term('normalized_insert_time', normalized_insert_time))
a_list = []
for _list in a:
    a_list += _list
print(a_list)

yichang = {'name': '状态异常爬虫'}
zhengchang = {'name': '状态正常爬虫'}
zhengchang['children'] = []
yichang['children'] = []

for a in a_list:
    _a = {}
    _a['name'] = a['project_name']
    _a['value'] = 1

    if a['project_status'] == 0:
        if not zhengchang['children']:
            zhengchang_class_dict = {}
            zhengchang_class_dict['name'] = a['project_class']
            zhengchang_class_dict['children'] = []
            zhengchang_class_dict['children'].append(_a)
            zhengchang['children'].append(zhengchang_class_dict)
        else:
            # 查询children_list内各个name值，如果存在，则存入该dict内，否则新建
            for index, zhengchang_class_dict in enumerate(zhengchang['children']):
                if zhengchang_class_dict['name'] == a['project_class'] and index < len(zhengchang['children']):
                    zhengchang_class_dict['children'].append(_a)
                    break
                else:
                    zhengchang_class_dict = {}
                    zhengchang_class_dict['name'] = a['project_class']
                    zhengchang_class_dict['children'] = []
                    zhengchang_class_dict['children'].append(_a)
                    zhengchang['children'].append(zhengchang_class_dict)
                    break

    else:
        if not yichang['children']:
            yichang_class_dict = {}
            yichang_class_dict['name'] = a['project_class']
            yichang_class_dict['children'] = []
            yichang_class_dict['children'].append(_a)
            yichang['children'].append(yichang_class_dict)
        else:
            for index, yichang_class_dict in enumerate(yichang['children']):
                if yichang_class_dict['name'] == a['project_class'] and index < len(yichang['children']):
                    yichang_class_dict['children'].append(_a)
                    break
                else:
                    yichang_class_dict = {}
                    yichang_class_dict['name'] = a['project_class']
                    yichang_class_dict['children'] = []
                    yichang_class_dict['children'].append(_a)
                    yichang['children'].append(yichang_class_dict)
                    break

reult_list = []
reult_list.append(yichang)
reult_list.append(zhengchang)
result = {'result': reult_list}
print(result)
