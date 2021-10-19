import calendar
import datetime
import pytz
import monthdelta
import re
from math import ceil


def str_to_timestamp(v, days=0):
    if not v:
        return 0
    return int(datetime.datetime.strptime((v + ' 00:00:00' if len(v) == 10 else v) + ' +0800',
                                          '%Y-%m-%d %H:%M:%S %z').timestamp()) + days * 86400


def utc_str_to_timestamp(v, days=0):
    if not v:
        return 0
    return int(datetime.datetime.strptime(v[0:19] + ' +0800', '%Y-%m-%dT%H:%M:%S %z').timestamp()) + days * 86400


def timestamp_to_str(v, days=0, full=False):
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.fromtimestamp(int(v) + 86400 * days, tz).strftime('%Y-%m-%d %H:%M:%S' if full else '%Y-%m-%d')


def timestamp_to_utc_str(v, days=0):
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.fromtimestamp(int(v) + 86400 * days, tz).strftime('%Y-%m-%dT%H:%M:%S+08:00')


def timestamp_to_utc_str_z(v, days=0):
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.datetime.fromtimestamp(int(v) + 86400 * days, tz).strftime('%Y-%m-%dT%H:%M:%SZ')


def timestamp_to_datetime(v, days=0):
    # tz = pytz.timezone('Asia/Shanghai')
    # return datetime.datetime.fromtimestamp(v + 86400 * days, tz)
    return datetime.datetime.fromtimestamp(int(v) + 86400 * days)


def timestamp_to_day_start(v, days=0):
    time_zone_second = 28800
    v += time_zone_second
    return int(v - (v % 86400) - time_zone_second + 86400 * days)


def timestamp_to_day_end(v, days=0):
    time_zone_second = 28800
    v += time_zone_second
    day_start = int(v - (v % 86400) - time_zone_second + 86400 * days)
    return day_start + 86400 - 1 - days * 86400


def timestamp_to_week_start(v, days=0):
    tz = pytz.timezone('Asia/Shanghai')
    t = datetime.datetime.fromtimestamp(timestamp_to_day_start(v, days), tz)
    return int((t - datetime.timedelta(t.weekday())).timestamp())


def timestamp_to_week_end(v, days=0):
    return timestamp_to_week_start(v, days) + 86400 * 7 - 1


def timestamp_to_month_start(v, days=0):
    tz = pytz.timezone('Asia/Shanghai')
    return int(str_to_timestamp(datetime.datetime.fromtimestamp(v + 86400 * days, tz).strftime('%Y-%m-01')))


def timestamp_to_month_end(v, days=0):
    month_start = timestamp_to_str(v, days)
    month_days = calendar.monthrange(int(month_start[0:4]), int(month_start[5:7]))[1]
    return int(datetime.datetime(int(month_start[0:4]), int(month_start[5:7]), month_days, 23, 59, 59, 0,
                                 tzinfo=pytz.timezone('Asia/Shanghai')).timestamp())


def datetime_diff_days(start, end):
    """
    :param start:str 2017-12-12
    :param end:str 2012-12-12
    :return:
    """
    return (datetime.datetime.strptime(start, '%Y-%m-%d') - datetime.datetime.strptime(end, '%Y-%m-%d')).days


def get_date_by_date_type(date, date_type):
    date = Date(date).year_week() if date_type == 'week' else Date(date).format(full=False)[:10] if date_type == 'day' else Date(date).format(full=False)[:7]
    return date


def get_now_timestamp_str():
    return str(int(datetime.datetime.now().timestamp()))


def str_to_utc_str(v):
    if not v:
        return None
    if len(v) == 10:
        return v + 'T00:00:00+08:00'
    return v.replace(' ', 'T') + '+08:00'


def range_date(start, end=None):
    if end is None:
        end = datetime.datetime.now()
    if isinstance(start, str):
        start = datetime.datetime.strptime(start, '%Y-%m-%d')
    if isinstance(end, str):
        end = datetime.datetime.strptime(end, '%Y-%m-%d')

    while start <= end:
        yield start.strftime('%Y-%m-%d')
        start = start + datetime.timedelta(1)
# timezone 'Asia/Shanghai'
tz = datetime.timezone(datetime.timedelta(hours=8))


def normalized_ctime(minute=5):
    '''规整当前时间,每5分钟范围内的时间取整'''
    current_minute = datetime.datetime.now().minute
    normalized_current_minute = current_minute // minute * minute
    normalized_current_time = datetime.datetime.now().replace(minute=normalized_current_minute, second=0)
    normalized_ctime_date = Date(normalized_current_time).format_es_utc_with_tz()
    return normalized_ctime_date

class Date:
    __tz = tz
    __z = datetime.datetime.now(__tz).strftime('%z')
    __es_z = ':'.join([__z[:3], __z[3:]])
    __time_zone_second = int(__z[:3]) * 3600

    def __init__(self, date=None):
        self.__origin_date = date
        self.__datetime = None

        if date is not None:
            self.__try_datetime(date) or self.__try_date_str(date) or self.__try_timestamp(date)

    @property
    def datetime(self):
        return self.__datetime

    def strftime(self, f, default=None):
        if not self.__datetime:
            return default
        return self.__datetime.strftime(f)

    def timestamp(self, default=0):
        if not self.__datetime:
            return default
        return int(self.__datetime.timestamp())

    def millisecond(self, default=0):
        if not self.__datetime:
            return default
        return int(self.__datetime.timestamp() * 1000)

    def format(self, default=None, full=True):
        if not self.__datetime:
            return default
        return self.__datetime.strftime('%Y-%m-%d %H:%M:%S' if full else '%Y-%m-%d')

    def format_es_utc_with_tz(self, default=None):
        if not self.__datetime:
            return default
        return self.__datetime.strftime('%Y-%m-%dT%H:%M:%S'+self.__es_z)

    def format_es_old_utc(self, default=None):
        if not self.__datetime:
            return default
        return self.__datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

    def format_es_utc(self, default=None):
        if not self.__datetime:
            return default
        return (self.__datetime - self.__datetime.utcoffset()).strftime('%Y-%m-%dT%H:%M:%SZ')

    def year_week(self, default=''):
        if not self.__datetime:
            return default
        year = self.__datetime.strftime('%Y')
        return '%s年第%02d周' % (year, self.year_week_number())

    def year_week_number(self, default=None):
        if not self.__datetime:
            return default
        day_of_year = int(self.strftime('%j'))
        # week = self.__datetime.strftime('%W')
        # week = int(week)+1
        return ceil((day_of_year + int(Date(self.__datetime).plus_days(-day_of_year).strftime('%w'))) / 7)


    def plus_seconds(self, seconds: float):
        if self.__datetime:
            self.__datetime = self.__datetime + datetime.timedelta(seconds=seconds)
        return self

    def plus_minutes(self, minutes: float):
        if self.__datetime:
            self.__datetime = self.__datetime + datetime.timedelta(minutes=minutes)
        return self

    def plus_hours(self, hours: float):
        if self.__datetime:
            self.__datetime = self.__datetime + datetime.timedelta(hours=hours)
        return self

    def plus_days(self, days: float):
        if self.__datetime:
            self.__datetime = self.__datetime + datetime.timedelta(days)
        return self

    def plus_weeks(self, weeks: float):
        if self.__datetime:
            self.__datetime = self.__datetime + datetime.timedelta(weeks=weeks)
        return self

    def plus_months(self, months: int):
        if self.__datetime:
            self.__datetime = self.__datetime + monthdelta.monthdelta(months)
        return self

    def to_hour_start(self):
        if self.__datetime:
            self.__datetime = self.__datetime.replace(minute=0, second=0)
        return self

    def to_hour_end(self):
        if self.__datetime:
            self.__datetime = self.__datetime.replace(minute=59, second=59)
        return self

    def to_day_start(self):
        if self.__datetime:
            self.__datetime = self.__datetime.replace(hour=0, minute=0, second=0)
        return self

    def to_day_end(self):
        if self.__datetime:
            self.__datetime = self.__datetime.replace(hour=23, minute=59, second=59)
        return self

    def to_week_start(self):
        if self.__datetime:
            self.__datetime = self.__datetime - datetime.timedelta(self.__datetime.weekday())
            self.to_day_start()
        return self

    def to_week_end(self):
        if self.__datetime:
            self.to_week_start().plus_weeks(1)
            self.__datetime = self.__datetime - datetime.timedelta(seconds=1)
            self.to_day_end()
        return self

    def to_month_start(self):
        if self.__datetime:
            self.__datetime = self.__datetime.replace(day=1, hour=0, minute=0, second=0)
        return self

    def to_month_end(self):
        if self.__datetime:
            self.to_month_start().plus_months(1)
            self.__datetime = self.__datetime - datetime.timedelta(seconds=1)
        return self

    def clone(self):
        return Date(self.__datetime)

    @staticmethod
    def generator_date(start, end, step_type='day', step=1):
        start = Date(start)
        end = Date(end)
        while start.timestamp() <= end.timestamp():
            yield start.clone()
            if step_type == 'day':
                start.plus_days(step)
            elif step_type == 'month':
                start.plus_months(step)
            elif step_type == 'week':
                start.plus_weeks(step)
            else:
                raise Exception('not support step type: %s', step_type)

    @staticmethod
    def delta_days(date1, date2):
        return Date.delta_seconds(date1, date2) / 86400

    @staticmethod
    def delta_hours(date1, date2):
        return Date.delta_seconds(date1, date2) / 3600

    @staticmethod
    def delta_minutes(date1, date2):
        return Date.delta_seconds(date1, date2) / 60

    @staticmethod
    def delta_seconds(date1, date2):
        return Date(date1).timestamp() - Date(date2).timestamp()

    def diff(self, date):
        return self.datetime.timestamp() - Date(date).datetime.timestamp()

    @classmethod
    def now(cls):
        return cls(datetime.datetime.now(cls.__tz))

    def __try_datetime(self, date):
        if isinstance(date, datetime.datetime):
            self.__datetime = datetime.datetime.fromtimestamp(date.timestamp(), self.__tz)
            return True
        elif isinstance(date, Date):
            self.__datetime = date.datetime
            return True
        else:
            return False

    def __try_timestamp(self, date):
        try:
            self.__datetime = datetime.datetime.fromtimestamp(float(date), self.__tz)
            return True
        except:
            return False

    def __try_date_str(self, date):
        if isinstance(date, str):
            if date.endswith('GMT'):
                self.__datetime = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S GMT')
                self.plus_seconds(self.__time_zone_second)
                return True
            if date.endswith('+0800'):
                self.__datetime = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S +0800')
                return True
            date = date[0:19].replace('T', ' ')
            len_str = len(date)
            arr = re.split('/|-|:| ', date)
            if len(arr) == 1 and len_str != 4:
                return False
            self.__datetime = datetime.datetime.strptime(
                '%s %s' % (' '.join(arr), self.__z),
                ' '.join(['%Y', '%m', '%d', '%H', '%M', '%S'][0:len(arr)]) + ' %z'
            )
            return True
        return False

    def __eq__(self, other):
        if not isinstance(other, Date):
            return self.datetime == Date(other).datetime
        return self.datetime == other.datetime

    def __lt__(self, other):
        if not isinstance(other, Date):
            return self.datetime < Date(other).datetime
        return self.datetime < other.datetime

    def __gt__(self, other):
        if not isinstance(other, Date):
            return self.datetime > Date(other).datetime
        return self.datetime > other.datetime

    def __repr__(self):
        return self.format()

