import xlrd


class ExcelReader:
    def __init__(self, file='', sheet_index=0, file_contents=None):
        self.file = file
        self.header = {}
        self.sheet_index = sheet_index
        self.find_header_row = False
        self.data = xlrd.open_workbook(self.file, file_contents=file_contents)

    def add_header(self, column_key, column_name):
        self.header.setdefault(column_key, {'column_name': column_name, 'column_index': None})
        return self

    def get_sheet_name(self):
        return self.data.sheet_by_index(self.sheet_index).name

    def get_row_values(self, rowx):
        return self.data.sheet_by_index(self.sheet_index).row_values(rowx)

    def get_result(self):
        return [_ for _ in self]

    def __iter__(self):
        table = self.data.sheet_by_index(self.sheet_index)
        nrows = table.nrows
        for i in range(nrows):
            row = [_.strip() if isinstance(_, str) else _ for _ in table.row_values(i)]
            if not self.find_header_row:
                for _key, _value in self.header.items():
                    if _value['column_name'] in row:
                        _value['column_index'] = row.index(_value['column_name'])
                if not list(filter(lambda x: x['column_index'] is None, self.header.values())):
                    self.find_header_row = True
                continue
            yield dict((_key, row[_value['column_index']]) for _key, _value in self.header.items())
