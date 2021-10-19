import fire
import os

from es.model.result import Result
from es.model.task import Task


class Cron:
    def clear(self):
        """
        清理es已经更新成功的过期数据
        :return:
        """
        Result().clear()
        Task().clear()

    def clear_useless_log_words(self, log_path, locate_words='No new message! RequestId'):
        """
        删除无用的日志打印，目前是针对中间件的打印日志：No new message! RequestId
        :param log_path: 需要删除相关内容的日志路径
        :param locate_words: 定位的字符串，用来定位需要删除的日志行
        :return:
        """
        if os.path.exists(log_path):
            print('存在路径:{},开始删除包含:{}的无用日志'.format(log_path, locate_words))
            saved_data = ''
            with open(log_path, 'r') as fr:
                all_data = fr.readlines()
                for _data in all_data:
                    if locate_words in _data:
                        continue
                    else:
                        saved_data += _data
            if saved_data:
                with open(log_path, 'w') as fw:
                    fw.write(saved_data)
                    print('成功删除包含:{}的日志行'.format(log_path))
        else:
            print('不存在存在路径:{}'.format(log_path))


if __name__ == '__main__':
    fire.Fire(Cron)
