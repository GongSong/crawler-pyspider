from pyspider.helper.date import Date, normalized_ctime
from monitor.page.alarm_rule import THRESHOLD_LAST_SYNC_TIME, THRESHOLD_DIFF_NUMBERS, more_than_threshold


class MonitorParasCollectionBase:
    '''
    收集监控所需的参数
    '''

    def __init__(self):
        self.es_model = ''
        self.spider = ''
        self.save_es_model = ''
        self.project_name = ''
        self.project_class = ''
        # 告警阈值及规则
        self.threshold_last_sync_time = THRESHOLD_LAST_SYNC_TIME
        self.threshold_diff_numbers = THRESHOLD_DIFF_NUMBERS
        self.rule_last_sync_time = more_than_threshold
        self.rule_diff_numbers = more_than_threshold

    def get_last_sync_time_compare(self):
        '''获取某个es_model内的最后更新时间对比'''
        now = Date.now().timestamp()
        normalized_now = normalized_ctime()
        now_date = Date.now().format_es_utc_with_tz()
        last_sync_time = self.es_model().get_last_sync_time()
        last_sync_time_date = Date(str(int(last_sync_time) / 1000)).format_es_utc_with_tz()
        # 相差时间取分钟，取整
        diff_time = (now - last_sync_time / 1000) // 60
        result = dict()
        result['insert_time'] = now_date
        result['normalized_insert_time'] = normalized_now
        result['project_class'] = self.project_class
        result['project_name'] = self.project_name
        result['inspection_item_name'] = '最后更新时间'
        result['inspection_item_detail'] = {}
        result['inspection_item_detail']['check_time'] = now_date
        result['inspection_item_detail']['last_sync_time'] = last_sync_time_date
        result['inspection_item_detail']['diff_time'] = int(diff_time)
        result['inspection_item_status'] = 1 if self.rule_last_sync_time(self.threshold_last_sync_time,
                                                                         result['inspection_item_detail'][
                                                                             'diff_time']) else 0
        return result

    def get_numbers_compare(self):
        now_date = Date.now().format_es_utc_with_tz()
        normalized_now = normalized_ctime()
        erp_numbers = self.spider().get_erp_numbers()
        es_numbers = self.es_model().get_es_numbers()
        result = dict()
        result['insert_time'] = now_date
        result['normalized_insert_time'] = normalized_now
        result['project_class'] = self.project_class
        result['project_name'] = self.project_name
        result['inspection_item_name'] = '总数量对比'
        result['inspection_item_detail'] = {}
        result['inspection_item_detail']['compared_numbers'] = int(erp_numbers)
        result['inspection_item_detail']['es_current_numbers'] = int(es_numbers)
        result['inspection_item_detail']['diff_numbers'] = es_numbers - erp_numbers
        result['inspection_item_status'] = 1 \
            if self.rule_diff_numbers(self.threshold_diff_numbers,
                                      result['inspection_item_detail']['diff_numbers'] /
                                      result['inspection_item_detail']['compared_numbers']) else 0
        return result

    def status_aggregation(self):
        save_last_sync_time_compare = self.get_last_sync_time_compare()
        save_numbers_compare = self.get_numbers_compare()
        project_status = 1 if save_last_sync_time_compare['inspection_item_status'] + save_numbers_compare[
            'inspection_item_status'] > 0 else 0
        save_last_sync_time_compare['project_status'] = project_status
        save_numbers_compare['project_status'] = project_status
        # print(save_last_sync_time_compare)
        # print(save_numbers_compare)
        self.save_es_model().update([save_last_sync_time_compare], async=True)
        self.save_es_model().update([save_numbers_compare], async=True)
