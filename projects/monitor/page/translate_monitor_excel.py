import re
import pandas as pd
from openpyxl.reader.excel import ExcelReader
from monitor.model.es.monitor_save2 import MonitorSave2
from pyspider.helper.es_query_builder import EsQueryBuilder
from pyspider.helper.excel import Excel

excel = Excel() \
    .add_header('normalized_insert_time', '规整插入时间') \
    .add_header('insert_time', '插入时间') \
    .add_header('project_class', '项目类名') \
    .add_header('project_name', '项目名称') \
    .add_header('project_status', '项目运行状态') \
    .add_header('inspection_item_name', '检测项名称') \
    .add_header('inspection_item_status', '检测项状态') \
    .add_header('check_time', '检测时间') \
    .add_header('last_sync_time', '最后更新时间') \
    .add_header('diff_time', '差异时间') \



product_list = MonitorSave2().scroll(page_size=1000)
for _d in product_list:
    for _dict in _d:
        try:
            normalized_insert_time = _dict['normalized_insert_time']
            insert_time = _dict['insert_time']
            project_class = _dict['project_class']
            project_name = _dict['project_name']
            project_status = _dict['project_status']
            inspection_item_name = _dict['inspection_item_name']
            inspection_item_status = _dict['inspection_item_status']
            check_time = _dict['inspection_item_detail']['check_time']
            last_sync_time = _dict['inspection_item_detail']['last_sync_time']
            diff_time = _dict['inspection_item_detail']['diff_time']

        except:
            continue
        the_list = {
            'normalized_insert_time': normalized_insert_time,
            'insert_time': insert_time,
            'project_class': project_class,
            'project_name': project_name,
            'project_status': project_status,
            'inspection_item_name': inspection_item_name,
            'inspection_item_status': inspection_item_status,
            'check_time': check_time,
            'last_sync_time': last_sync_time,
            'diff_time': diff_time
        }
        excel.add_data(the_list)

    with open('data.xlsx', 'wb') as file:
        file.write(excel.execute())
