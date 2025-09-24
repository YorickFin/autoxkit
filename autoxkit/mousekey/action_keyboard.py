import ctypes
import time
from .constants import Hex_Key_Code as HKC

def key_down(key_name: str):
    """模拟按下按键"""
    ctypes.windll.user32.keybd_event(HKC[key_name], 0, 0, 0)

def key_up(key_name: str):
    """模拟释放按键"""
    ctypes.windll.user32.keybd_event(HKC[key_name], 0, 2, 0)

def key_click(key_name: str, duration=0.04):
    """模拟单击按键"""
    key_down(key_name)
    time.sleep(duration)
    key_up(key_name)

def key_combination(keys: list, duration=0.1):
    """模拟组合键"""

    for key_name in keys:
        key_down(key_name)
        time.sleep(0.04)

    # 保持组合键状态
    time.sleep(duration)

    for key_name in reversed(keys):
        key_up(key_name)
        time.sleep(0.04)