
class LocalMqBase:
    def __init__(self, data):
        self._data = data
        self._msg = ""
        self._data_id = ""
        self._publish_time = ""
        self._publish_service = ""
        self._message_tag = ""
        self._action = ""

    def print_basic_info(self):
        """
        打印接受到的基本数据
        :return:
        """
        print("data:", self._data)
