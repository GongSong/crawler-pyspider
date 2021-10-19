from monitor.model.es.monitor_save2 import MonitorSave2
from pyspider.helper.date import Date
from pyspider.helper.es_query_builder import EsQueryBuilder




# a_list = [{'normalize_insert_time': '2019-06-16T20:05:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:10:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T20:15:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:20:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:25:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:30:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:35:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T20:40:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T20:45:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:50:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:00:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:05:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T21:10:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:15:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T21:20:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:25:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '订单爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:05:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:10:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:15:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:20:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T20:25:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:30:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:35:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:40:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T20:45:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:50:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T20:55:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:00:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:05:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:10:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T21:15:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0},
#           {'normalize_insert_time': '2019-06-16T21:20:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 1},
#           {'normalize_insert_time': '2019-06-16T21:25:00+08:00',
#            'project_class': '万里牛爬虫',
#            'project_name': '库存爬虫',
#            'project_status': 0}
#           ]

a = MonitorSave2().scroll(
                    EsQueryBuilder()
                    .range('normalized_insert_time', Date().now().plus_days(-1)
                    .format_es_old_utc(), None),
                        page_size=2500
                    )
a_list = []
for _list in a:
    a_list += _list
print(a_list)


final_json = {'insert_time': [],
              'items': {}
              }

start_time = '2019-06-24T16:00:00+08:00'
end_time = '2019-06-24T16:35:00+08:00'
i = -1
while True:
    i += 1
    aa = Date(start_time).plus_minutes(i * 5).format_es_utc_with_tz()
    if aa > end_time:
        break
    else:
        final_json['insert_time'].append(aa)

for a in a_list:
    if not final_json['items'].get(a['project_name'], ''):
        final_json['items'][a['project_name']] = []
        final_json['items'][a['project_name']].append(a['project_status'])
    else:
        final_json['items'][a['project_name']].append(a['project_status'])

print(final_json)

series = []
for index, name in enumerate(list(final_json['items'].keys())):
    _series_dict = {}
    _series_dict['name'] = name
    _series_dict['type'] = 'line'
    _series_dict['data'] = [i + index * 1.5 for i in final_json['items'][name]]
    series.append(_series_dict)

print(series)
option = {
    'title': {
        'text': '爬虫状态展示'
    },
    'legend': {
        'data': list(final_json['items'].keys())
    },
    'toolbox': {
        'feature': {
            'saveAsImage': {},
            'dataZoom': {
                'yAxisIndex': 'false'
            }
        }
    },
    'grid': {
        'left': '3%',
        'right': '4%',
        'bottom': '8%',
        'containLabel': 'true'
    },
    'xAxis': [
        {
            'type': 'category',
            'boundaryGap': 'false',
            'data': final_json['insert_time']
        }
    ],
    'yAxis': [
        {
            'type': 'value',
            'min': 0,
            'max': 3,
        }
    ],
    'dataZoom': [{
        'type': 'inside',
        'start': 20,
        'end': 100
    }, {
        'start': 0,
        'end': 100,
        'handleSize': '60%',
    }],
    'series': series
}

print(option)
