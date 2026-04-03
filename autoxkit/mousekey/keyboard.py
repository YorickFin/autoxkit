import ctypes
import time
from .input import Input_I, Input, KeyBdInput
from ..constants import Hex_Key_Code as HKC

user32 = ctypes.windll.user32
SendInput = user32.SendInput
MapVirtualKey = user32.MapVirtualKeyW

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001
MAPVK_VK_TO_VSC = 0

EXTENDED_KEYS = {
    "Left", "Up", "Right", "Down",
    "Insert", "Delete", "Home", "End", "PgUp", "PgDown",
    "Rctrl", "Ralt",
    "Volume_Down", "Volume_Up", "Volume_Mute", "Launch_App2",
}

class KeyBoard:
    def __init__(self, compat=False):
        self.compat = compat

    def _key_down_compat(self, key_name: str):
        vk = HKC[key_name]
        scan = MapVirtualKey(vk, MAPVK_VK_TO_VSC)
        user32.keybd_event(vk, scan, 0, 0)

    def _key_down_input(self, key_name: str):
        vk = HKC[key_name]
        scan = MapVirtualKey(vk, MAPVK_VK_TO_VSC)

        flags = KEYEVENTF_SCANCODE
        if key_name in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY

        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, scan, flags, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def key_down(self, key_name: str):
        if self.compat:
            self._key_down_compat(key_name)
        else:
            self._key_down_input(key_name)

    def _key_up_compat(self, key_name: str):
        vk = HKC[key_name]
        scan = MapVirtualKey(vk, MAPVK_VK_TO_VSC)
        user32.keybd_event(vk, scan, KEYEVENTF_KEYUP, 0)

    def _key_up_input(self, key_name: str):
        vk = HKC[key_name]
        scan = MapVirtualKey(vk, MAPVK_VK_TO_VSC)

        flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        if key_name in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY

        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, scan, flags, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def key_up(self, key_name: str):
        if self.compat:
            self._key_up_compat(key_name)
        else:
            self._key_up_input(key_name)

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
