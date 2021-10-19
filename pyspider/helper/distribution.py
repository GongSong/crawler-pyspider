class Distribution:
    def __init__(self, number_list: list):
        """
        :param number_list: 给出数据的区间节点，类似：[5,10,20,30,40,50]
        """
        self.__number_list = number_list
        # 第一个区间的开始值
        self.__number_start = 0
        # 50+ 和 51+ 的区别, 只影响返回不参与比对, 加一看起来比较合理
        self.__end_plus = 1
        # 区间开始节点累加
        self.__interval_start_plus = 1
        # 区间格式
        self.__interval_format = '%d-%d'
        # 最后一个区间的格式
        self.__more_than_format = '%d+'
        # 如果0的输出格式不设置自动合并到第一个区间
        self.__zero_format = None

    def get_distribution(self, value):
        """
        对输入值判断应该属于哪个区间，返回对应区间,比如：0-5， 6-10，11-20
        :param value:
        :return:
        """
        # 如果0是独立区间，直接返回0分布
        if self.__zero_format and value == 0:
            return self.__zero_format % value
        for _i, _value in enumerate(self.__number_list):
            # 如果输入值小余等于节点值说明属于上一个区间的数据
            if value <= _value:
                # 如果是第一个区间可以自定义第一个区间的起始值, 也就是是可以
                if _i == 0:
                    return self.__interval_format % (self.__number_start, _value)
                else:
                    return self.__interval_format % (self.__number_list[_i - 1] + self.__interval_start_plus, _value)
        # 输入值大于所有节点值，只能是最后一个区间了
        return self.__more_than_format % (self.__number_list[-1] + self.__end_plus)

    def get_all_distribution(self):
        """
        获取所有区间的列表, 列：['0-5', '6-10', '11-20', '21+']
        :return:
        """
        result = []
        if self.__zero_format:
            result.append(self.get_distribution(0))
        for _ in self.__number_list:
            result.append(self.get_distribution(_))
        result.append(self.get_distribution(self.__number_list[-1] + 1))
        return result

    def set_number_list(self, number_list):
        """
        给出数据的区间节点，类似：[5,10,20,30,40,50]
        :param number_list:
        :return:
        """
        self.__number_list = number_list
        return self

    def set_number_start(self, number_start):
        """
        初始区间的最小值,一般不是0就是1, 默认是0
        作用：0 => 0-5, 1 => 1-5
        :param number_start:
        :return:
        """
        self.__number_start = number_start
        return self

    def set_interval_start_plus(self, interval_start_plus):
        """
        对于区间的开始值是否加一
        :param interval_start_plus:
        :return:
        """
        self.__interval_start_plus = interval_start_plus
        return self

    def set_interval_format(self, interval_format):
        """
        设置区间分布的输出格式,默认: %d-%d
        :param interval_format:
        :return:
        """
        self.__interval_format = interval_format
        return self

    def set_more_than_format(self, more_than_format):
        """
        设置最后一个大于等于区间的输出格式,默认: %d+
        :param more_than_format:
        :return:
        """
        self.__more_than_format = more_than_format
        return self

    def set_end_plus(self, end_plus):
        """
        最后一个区间是否加1, 默认加1
        :param end_plus:
        :return:
        """
        self.__end_plus = end_plus
        return self

    def set_zero_format(self, zero_format):
        """
        设置0区间, 如果0不需要独立区间请不要设置, 值类似: %d
        :param zero_format:
        :return:
        """
        self.__zero_format = zero_format
        if zero_format:
            self.set_number_start(1)
        return self
