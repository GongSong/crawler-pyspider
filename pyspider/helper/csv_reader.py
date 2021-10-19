import csv


class CsvReader:
    def __init__(self, file='', file_contents=None):
        self.file = file
        self.header = {}
        self.find_header_row = False
        if file_contents:
            self.data = csv.reader(file_contents)
        else:
            with open(file, newline='') as csvfile:
                self.data = csv.reader(csvfile)

    def add_header(self, column_key, column_name):
        self.header.setdefault(column_key, {'column_name': column_name, 'column_index': None})
        return self

    def get_result(self):
        return [_ for _ in self]

    def __iter__(self):
        for row in self.data:
            row = [_.strip() if isinstance(_, str) else _ for _ in row[:]]
            if not self.find_header_row:
                for _key, _value in self.header.items():
                    if _value['column_name'] in row:
                        _value['column_index'] = row.index(_value['column_name'])
                if not list(filter(lambda x: x['column_index'] is None, self.header.values())):
                    self.find_header_row = True
                continue
            if len(row) < len(self.header):
                continue
            yield dict((_key, row[_value['column_index']]) for _key, _value in self.header.items())
