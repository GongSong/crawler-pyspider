import random
import time
import traceback

from selenium.webdriver import ActionChains
from cookie.config import TMALL_TRACE_POOL
from pyspider.core.model.storage import default_storage_redis


class TmallSlideCaptchaCrack:
    """
    天猫淘宝滑动验证码破解
    """

    @staticmethod
    def check_slide_bar(driver, id_element='', class_element=''):
        """
        判断是否有滑动验证码,如有则破解滑动验证码
        :param driver: webdriver 实例
        :param id_element: 滑动验证码的 ID html标签
        :param class_element: 滑动验证码的 class html标签
        :return: True or False
        """
        try:
            if id_element:
                driver.find_element_by_id(id_element).click()
                print('有滑动验证码')
                return True
            elif class_element:
                driver.find_element_by_class_name(class_element).click()
                print('有滑动验证码')
                return True
            else:
                print('没有找到滑动验证码')
                return False
        except Exception as e:
            print(e)
            print('没有找到滑动验证码')
            return False

    @staticmethod
    def crack_slide_bar(driver, id_element='', class_element=''):
        """
        滑动破解验证码
        :param driver: webdriver 实例
        :param id_element: 滑动验证码的 ID html标签
        :param class_element: 滑动验证码的 class html标签
        :return: True or False
        """
        success_slide_bar = '//span[@data-nc-lang="_yesTEXT"]'
        trace = random.choice(TMALL_TRACE_POOL)
        print('开始破解滑动验证码')
        try:
            if id_element:
                slider_bar = driver.find_element_by_id(id_element)
            elif class_element:
                slider_bar = driver.find_element_by_class_name(id_element)
            else:
                print('传入的滑动验证码html标签')
                return
            offset = []
            # 轨迹转成速度（每秒偏移量）
            for i in range(1, len(trace)):
                c = random.randint(1, 9)
                x_offset = trace[i][0] - trace[i - 1][0]
                y_offset = trace[i][1] - trace[i - 1][1]
                if c == 8:
                    x_offset += 1
                elif c == 6:
                    x_offset -= 1
                elif c == 2:
                    y_offset += 1
                elif c == 3:
                    y_offset -= 1
                offset.append((x_offset, y_offset))
            print('轨迹转成速度,每秒偏移量:', offset)
            action = ActionChains(driver)
            action.click_and_hold(slider_bar)
            for x in offset:
                action.move_by_offset(xoffset=x[0], yoffset=x[1])
            time.sleep(0.5)
            action.release(slider_bar).perform()
            time.sleep(1)
            # 查看是否滑动破解成功
            crack_success = driver.find_element_by_xpath(success_slide_bar).text
            print('滑动破解成功')
            success_time = int(default_storage_redis.hget(str(trace), 'success').decode(
                'utf8')) if default_storage_redis.hget(str(trace), 'success') else 0
            default_storage_redis.hset(str(trace), 'success', success_time + 1)
            return True
        except Exception:
            print('验证未通过或Redis保存失败')
            print(traceback.format_exc())
            try:
                fail_time = int(default_storage_redis.hget(str(trace), 'fail').decode(
                    'utf8')) if default_storage_redis.hget(str(trace), 'fail') else 0
                default_storage_redis.hset(str(trace), 'fail', fail_time + 1)
            except Exception:
                print('Redis保存失败')
                print(traceback.format_exc())
            return False
