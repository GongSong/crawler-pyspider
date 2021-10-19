from pyspider.helper.date import Date
from pyspider.helper.logstash_formatter import LogstashFormatterV1
from pyspider.config import config
import logging
import logging.handlers


class Log:
    FORMAT = LogstashFormatterV1()

    def __init__(self):
        self.error_handler = self.create_file_handler('error', 'ERROR')
        self.all_handler = self.create_file_handler('all', config.get('log', 'log_level'))
        self.console_handler = self.create_console_handler()
        self.log_level = config.get('log', 'log_level')

    def create_file_handler(self, file_name, log_level=None):
        handle = logging.handlers.WatchedFileHandler('%s/%s.log' % (config.get('log', 'log_dir'), file_name))
        handle.setFormatter(self.FORMAT)
        handle.setLevel(log_level if log_level else self.log_level)
        return handle

    def create_console_handler(self):
        console = logging.StreamHandler()
        console.setFormatter(self.FORMAT)
        console.setLevel(logging.DEBUG)
        return console

    def create_logger(self, logger_name):
        l = logging.getLogger(logger_name)
        l.setLevel(config.get('log', 'log_level'))
        l.propagate = False
        l.addHandler(self.error_handler)
        l.addHandler(self.all_handler)
        l.addHandler(self.create_file_handler(logger_name))
        if config.getint('log', 'console'):
            l.addHandler(self.console_handler)
        return l


log = Log()
logger = log.create_logger('app')
scheduler_logger = log.create_logger(config.CONST_PROCESS_SCHEDULER)
fetcher_logger = log.create_logger(config.CONST_PROCESS_FETCHER)
processor_logger = log.create_logger(config.CONST_PROCESS_PROCESSOR)
result_logger = log.create_logger(config.CONST_PROCESS_RESULT)
webui_logger = log.create_logger(config.CONST_PROCESS_WEBUI)
phantomjs_logger = log.create_logger(config.CONST_PROCESS_PHANTOMJS)
mq_logger = log.create_logger('mq')
werkzeug_logger = log.create_logger('werkzeug')
mitmproxy_logger = log.create_logger('mitmproxy')
daily_log = log.create_logger("daily_log:{}".format(Date.now().format(full=False)))
cron_log = log.create_logger("cron")


def task_log(task, message='', extra=None):
    extra = {'task': extra} if extra else None
    logging.getLogger(config.get_process_name()).info(message, task, extra=extra)


def task_monitor(task, status):
    url = task['url']
    page_name = task.get('fetch', {}).get('save', {}).get('page_name')
    if not page_name:
        page_name = task.get('track', {}).get('fetch', {}).get('page_name')
    content_len = task.get('track', {}).get('fetch', {}).get('content_len')
    fetch_time = task.get('track', {}).get('fetch', {}).get('time')
    fetch_status_code = task.get('track', {}).get('fetch', {}).get('status_code')
    fetch_error = task.get('track', {}).get('fetch', {}).get('error')
    fetch_ok = task.get('track', {}).get('fetch', {}).get('ok')
    process_time = task.get('track', {}).get('process', {}).get('time')
    process_exception = task.get('track', {}).get('process', {}).get('exception')
    process_follows = task.get('track', {}).get('process', {}).get('follows')
    process_ok = task.get('track', {}).get('process', {}).get('ok')
    # schedule 和 fetch 不一定可以拿到
    # schedule_retries = task.get('schedule', {}).get('retries')
    # schedule_priority = task.get('schedule', {}).get('priority')
    # schedule_age = task.get('schedule', {}).get('age')
    # fetch_proxy = task.get('fetch', {}).get('proxy')
    if url.startswith('data:'):
        fetch_type = 'data'
    elif task.get('fetch', {}).get('fetch_type') in ('js', 'phantomjs'):
        fetch_type = 'phantomjs'
    elif task.get('fetch', {}).get('fetch_type') in ('splash', ):
        fetch_type = 'splash'
    else:
        fetch_type = 'http'

    scheduler_logger.warning('task_monitor', extra={
        'data': {
            'project': task['project'],
            'taskid': task['taskid'],
            'url': task['url'],
            'process': config.get_process_name(),
            'page_name': page_name if page_name else '',
            'status': status,
            'content_len': content_len if content_len else 0,
            # 'schedule_retries': schedule_retries if schedule_retries else 0,
            # 'schedule_priority': schedule_priority if schedule_priority else 0,
            # 'schedule_age': schedule_age if schedule_age else 0,
            'fetch_time': fetch_time if fetch_time else 0,
            'fetch_type': fetch_type,
            # 'fetch_proxy': fetch_proxy,
            'fetch_status_code': fetch_status_code,
            'fetch_error': fetch_error,
            'fetch_ok': 1 if fetch_ok else 0,
            'process_time': process_time if fetch_time else 0,
            'process_exception': process_exception,
            'process_follows': process_follows if process_follows else 0,
            'process_ok': 1 if process_ok else 0,
        }
    })
