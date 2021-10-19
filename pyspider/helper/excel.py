import os
import xlsxwriter
import uuid
from functools import reduce
from pyspider.config import config


class Excel:
    def __init__(self):
        self.header = []
        self.data = []
        self.unique_key = self.rand_unique_key()
        self.sheet_list = []
        self.sheet_name = None

    def new_sheet(self, name=None):
        sheet = Sheet(name)
        self.sheet_list.append(sheet)
        return sheet

    def execute(self, data=None):
        if data:
            self.data = data
        file_path_tmp = '%s/%s.xls' % (config.get('log', 'log_dir'), self.unique_key)
        # 创建Excel文件
        workbook = xlsxwriter.Workbook(file_path_tmp)
        if self.header:
            self.__execute_sheet(workbook, self.header, self.data, self.sheet_name)
        for _sheet in self.sheet_list:
            self.__execute_sheet(workbook, _sheet.header, _sheet.data, _sheet.name)
        workbook.close()
        with open(file_path_tmp, 'rb+') as f:
            bin_data = f.read()
        os.unlink(file_path_tmp)
        return bin_data

    def export_file(self, data=None, file_name="demo"):
        """
        导出表格
        :param data:
        :param file_name:
        """
        if data:
            self.data = data
        file_path_tmp = '%s/%s.xls' % (config.get('log', 'log_dir'), file_name)
        # 创建Excel文件
        workbook = xlsxwriter.Workbook(file_path_tmp)
        if self.header:
            self.__execute_sheet(workbook, self.header, self.data, self.sheet_name)
        for _sheet in self.sheet_list:
            self.__execute_sheet(workbook, _sheet.header, _sheet.data, _sheet.name)
        workbook.close()

    def add_sheet(self, sheet):
        self.sheet_list.append(sheet)

    def __execute_sheet(self, workbook, header, data, name=None):
        # 添加工作表
        worksheet = workbook.add_worksheet(name)

        # 添加bold字体样式
        bold = workbook.add_format({'bold': 1})
        for _index, _value in enumerate(header):
            level = 0
            worksheet.set_column(_index, _index, int(_value.get('width', 20)), options={'level': level})
            worksheet.write(0, _index, _value.get('title', ''), bold)
        for _row_index, _row in enumerate(data):
            for _col_index, _col_info in enumerate(header):
                worksheet.write(_row_index+1, _col_index, self.get_value(_row, _col_info.get('key')))

    def set_header(self, header):
        self.header = header
        return self

    def add_header_list(self, header_list):
        for x in header_list:
            self.header.append({'key': str(x['key']), 'title': str(x['name']), 'width': 20})
        return self

    def add_header(self, key, title, width=20):
        self.header.append({
            'key': key,
            'title': title,
            'width': width
        })
        return self

    def set_data(self, data):
        self.data = data
        return self

    def add_data(self, record):
        self.data.append(record)
        return self

    def set_sheet_name(self, sheet_name):
        self.sheet_name = sheet_name
        return self

    @staticmethod
    def get_value(d, k):
        r = reduce(lambda x, y: x.get(y, {}), k.split('.'), d)
        if r == {}:
            return ''
        return r

    @staticmethod
    def rand_unique_key():
        return uuid.uuid4().hex


class Sheet:
    def __init__(self, name=None):
        self.header = []
        self.data = []
        self.name = name

    def set_name(self, name):
        self.name = name
        return self

    def set_header(self, header):
        self.header = header
        return self

    def add_header(self, key, title, width=20):
        self.header.append({
            'key': key,
            'title': title,
            'width': width
        })
        return self

    def set_data(self, data):
        self.data = data
        return self

    def add_data(self, record):
        self.data.append(record)
        return self

