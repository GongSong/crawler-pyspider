import pyautogui
import fire
import time


class AutoScrpit:
    def random_click_target_button(self):
        """
        随机点击屏幕中央的点，最后点击指定的目标点;
        :return:
        """
        # 随机点击屏幕中央附近的点
        pyautogui.moveTo(-708, 829, duration=2)
        pyautogui.click()

        # 目标位置
        target = [564, 547]
        pyautogui.moveTo(target[0], target[1], duration=2)
        pyautogui.click()
        print('auto click')

    def get_current_position(self):
        """
        返回当前光标的位置
        :return:
        """
        print('20s 后开始获取当前鼠标的位置')
        time.sleep(20)
        current = pyautogui.position()
        print(current)


if __name__ == '__main__':
    fire.Fire(AutoScrpit)
