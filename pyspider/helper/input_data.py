import hashlib

from pyspider.helper.string import merge_str


class InputData:
    """
    get value from dict
    """

    def __init__(self, d):
        self.d = {}
        if d:
            self.d = d

    def get_int(self, key, default=None):
        """
        format int
        :param key:
        :param default:
        :return: int
        """
        return int(self.d.get(key)) if (self.d.get(key) or self.d.get(key) == 0) else default

    def get_str(self, key, default=None):
        """
        format str
        :param key:
        :param default:
        :return:
        """
        return str(self.d.get(key)).strip() if self.d.get(key) else default

    def get_array(self, key, default=None):
        """
        format array
        :param key:
        :param default:
        :return:
        """
        return list(self.d.get(key)) if self.d.get(key) else default

    def get(self, key, default=None):
        """
        format array
        :param key:
        :param default:
        :return:
        """
        return InputData(dict(self.d.get(key)) if self.d.get(key) else default)

    def pre_match_array(self, key, default=None):
        """
        format array
        :param key:
        :param default:
        :return:
        """
        result = []
        for _key, _value in self.d.items():
            if _key.startswith(key):
                result.append(_value)
        return result if result else default

    def get_array_by_str(self, key, sep, default=None):
        """
        str to array
        :param key:
        :param sep:
        :param default:
        :return:
        """
        return str(self.d.get(key)).split(sep) if self.d.get(key) else default

    def get_float(self, key, default=None):
        """
        format float
        :param key:
        :param default:
        :return:
        """
        return float(self.d.get(key)) if (self.d.get(key) or self.d.get(key) == 0) else default

    def get_data(self):
        """
        get all data
        :return:
        """
        return self.d

    def get_sign(self, salt='', keys=None):
        """
        get sign
        :return:
        """
        if not keys:
            keys = self.d.keys()
        str_list = [merge_str('_salt', salt)]
        for _key in keys:
            str_list.append(merge_str(_key, self.d.get(_key)))
        m = hashlib.md5()
        m.update('&'.join(sorted(str_list)).encode('utf-8'))
        return m.hexdigest()
