import ctypes
import time
from .constants import Hex_Key_Code as HKC

class KeyBoardControl:

    def key_down(self, key_name: str):
        """模拟按下按键"""
        ctypes.windll.user32.keybd_event(HKC[key_name], 0, 0, 0)

    def key_up(self, key_name: str):
        """模拟释放按键"""
        ctypes.windll.user32.keybd_event(HKC[key_name], 0, 2, 0)

    def key_click(self, key_name: str, delay: float=0.02):
        """模拟单击按键"""
        self.key_down(key_name)
        time.sleep(delay)
        self.key_up(key_name)

    def key_combination(self, keys: list):
        """模拟组合键"""

        for key_name in keys:
            self.key_down(key_name)
            time.sleep(0.02)

        # 保持组合键状态
        time.sleep(0.1)

        for key_name in reversed(keys):
            self.key_up(key_name)
            time.sleep(0.02)