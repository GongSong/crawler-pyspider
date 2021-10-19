import time


class Retry:
    def retry(times, sleep_time=0):
        '''
        重试的装饰器 times为重试次数。被装饰方法成功时候需返回True，失败时需返回False。
        :return:
        '''
        def out_function(funtion):
            # 总的重试次数
            RETRY_TIMES = times
            # 当前重试次数
            retry_time = 0

            def wrapped(*args, **kwargs):
                nonlocal retry_time
                result = funtion(*args, **kwargs)
                if result is False:
                    retry_time += 1
                    if retry_time < RETRY_TIMES:
                        time.sleep(sleep_time)
                        print('重试第{}次 开始重试'.format(retry_time))
                        return wrapped(*args, **kwargs)
                    else:
                        print('重试第{}次 最终仍失败'.format(retry_time))
                        retry_time = 0
                        return False
                elif result == 'other':
                    retry_time = 0
                    return 'other'
                else:
                    retry_time = 0
                    return True
            return wrapped
        return out_function

    def retry_parameter(times, sleep_time=0, rate=0.1):
        '''
        重试的装饰器 times为重试次数。被装饰方法成功时候需返回True，失败时需返回False。第一个参数不为rate、True、False时，不重试。
        :return:
        '''

        def out_function(funtion):
            # 总的重试次数
            RETRY_TIMES = times - 1

            def wrapped(*args, **kwargs):
                for i in range(RETRY_TIMES + 1):
                    result = funtion(*args, **kwargs)
                    result_handle = result[0] if type(result) == tuple else result
                    if result_handle is False:
                        time.sleep(sleep_time)
                        print('开始重试第{}次'.format(i + 1))
                    elif result_handle == 'rate':
                        time.sleep(sleep_time * rate)
                        print('开始重试第{}次'.format(i + 1))
                    else:
                        return result
                print('重试{}次 最终仍失败'.format(RETRY_TIMES + 1))
                return result

            return wrapped

        return out_function
