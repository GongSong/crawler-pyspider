import os

import pyspider.result.result_worker
from pyspider.helper.logging import task_log, result_logger
from pyspider.config import config
from pyspider.libs.utils import load_object, pickle_loads, unicode_obj


class ResultWorker(pyspider.result.result_worker.ResultWorker):
    def __init__(self, resultdb, inqueue):
        super(ResultWorker, self).__init__(resultdb, inqueue)
        self.__result_instances = {}
        self.__init_result_instances()

    def on_result(self, task, result):
        task_log(task, 'on result')
        '''Called every result'''
        if not result:
            return
        if 'taskid' in task and 'project' in task and 'url' in task:
            pyspider.result.result_worker.logger.info('result %s:%s %s -> %.30r' % (
                task['project'], task['taskid'], task['url'], result))
            if task['project'] in self.__result_instances:
                self.__result_instances[task['project']].update(task, result)
            if isinstance(result, dict) and 'binary' in result:
                result['binary'] = len(result['binary'])

            self.resultdb.save(
                project=task['project'],
                taskid=task['taskid'],
                url=task['url'],
                result=unicode_obj(result)
            )
            save = task.get('fetch', {}).get('save', {})
            if isinstance(save, dict) and 'handler_page' in save:
                handler_page = pickle_loads(save['handler_page'])
                handler_page.result_hook(result, task)
                for _ in handler_page.get_follows():
                    _.enqueue()
            return
        else:
            pyspider.result.result_worker.logger.warning('result UNKNOW -> %.30r' % result)
            return

    def __init_result_instances(self):
        projects_dir = config.get('projects', 'dir')
        for _project in os.listdir(projects_dir):
            if os.path.exists(os.path.join(projects_dir, _project, 'result.py')):
                try:
                    cls = load_object('%s.result.Result' % _project)
                    self.__result_instances[_project] = cls()
                    result_logger.info('load result cls: %s' % _project)
                except:
                    result_logger.error('load result cls err: %s' % _project)
