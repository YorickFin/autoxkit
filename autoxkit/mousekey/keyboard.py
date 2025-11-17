import ctypes
import time
from .constants import Hex_Key_Code as HKC

user32 = ctypes.windll.user32

# flags
KEYEVENTF_KEYUP = 0x0002

# MapVirtualKey
MapVirtualKey = user32.MapVirtualKeyW

class KeyBoard:

    def key_down(self, key_name: str):
        vk = HKC[key_name]
        scan = MapVirtualKey(vk, 0)
        user32.keybd_event(vk, scan, 0, 0)

    def key_up(self, key_name: str):
        vk = HKC[key_name]
        scan = MapVirtualKey(vk, 0)
        user32.keybd_event(vk, scan, KEYEVENTF_KEYUP, 0)

    def key_click(self, key_name: str, delay=0.02):
        self.key_down(key_name)
        time.sleep(delay)
        self.key_up(key_name)

    def key_combination(self, keys: list):
        for key in keys:
            self.key_down(key)
            time.sleep(0.01)
        time.sleep(0.1)
        for key in reversed(keys):
            self.key_up(key)
            time.sleep(0.01)
