import time
import ctypes
from ctypes import wintypes
from ..constants import Hex_Key_Code as HKC

user32 = ctypes.windll.user32

# 定义 Windows API 函数
SendMessage = user32.SendMessageW
SendMessage.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
SendMessage.restype = wintypes.LPARAM

PostMessage = user32.PostMessageW
PostMessage.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
PostMessage.restype = wintypes.BOOL

MapVirtualKey = user32.MapVirtualKeyW
MapVirtualKey.argtypes = [wintypes.UINT, wintypes.UINT]
MapVirtualKey.restype = wintypes.UINT

# 定义窗口消息常量
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_SYSKEYUP = 0x0105
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEMOVE = 0x0200
WM_MOUSEWHEEL = 0x020A

# 定义鼠标消息参数
MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0010

# 定义坐标转换宏
MAKELPARAM = lambda x, y: (y << 16) | (x & 0xFFFF)  # noqa: E731


class WindowAction:
    def __init__(self, hwnd: int = None):
        self.hwnd = hwnd if hwnd else None

    def send_key_down(self, key_name: str, use_post: bool = False):
        """发送按键按下消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        vk = HKC[key_name]
        scan = MapVirtualKey(vk, 0)
        lparam = (scan << 16) | 1

        if use_post:
            PostMessage(self.hwnd, WM_KEYDOWN, vk, lparam)
        else:
            SendMessage(self.hwnd, WM_KEYDOWN, vk, lparam)

    def send_key_up(self, key_name: str, use_post: bool = False):
        """发送按键释放消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        vk = HKC[key_name]
        scan = MapVirtualKey(vk, 0)
        lparam = (scan << 16) | 0xC0000001

        if use_post:
            PostMessage(self.hwnd, WM_KEYUP, vk, lparam)
        else:
            SendMessage(self.hwnd, WM_KEYUP, vk, lparam)

    def send_key_click(self, key_name: str, delay: float = 0.02, use_post: bool = False):
        """发送按键点击消息（按下+释放）"""
        self.send_key_down(key_name, use_post)
        time.sleep(delay)
        self.send_key_up(key_name, use_post)

    def send_key_combination(self, keys: list, use_post: bool = False):
        """发送组合键消息"""
        for key in keys:
            self.send_key_down(key, use_post)
            time.sleep(0.01)
        time.sleep(0.01)
        for key in reversed(keys):
            self.send_key_up(key, use_post)
            time.sleep(0.01)

    def send_text(self, char: str, use_post: bool = False):
        """发送文本消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        for c in char:
            if use_post:
                PostMessage(self.hwnd, WM_CHAR, ord(c), 0)
            else:
                SendMessage(self.hwnd, WM_CHAR, ord(c), 0)

    def send_mouse_move(self, x: int, y: int, use_post: bool = False):
        """发送鼠标移动消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(x, y)

        if use_post:
            PostMessage(self.hwnd, WM_MOUSEMOVE, 0, lparam)
        else:
            SendMessage(self.hwnd, WM_MOUSEMOVE, 0, lparam)

    def send_left_down(self, x: int, y: int, use_post: bool = False):
        """发送鼠标左键按下消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(x, y)

        if use_post:
            PostMessage(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        else:
            SendMessage(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)

    def send_left_up(self, x: int, y: int, use_post: bool = False):
        """发送鼠标左键释放消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(x, y)

        if use_post:
            PostMessage(self.hwnd, WM_LBUTTONUP, 0, lparam)
        else:
            SendMessage(self.hwnd, WM_LBUTTONUP, 0, lparam)

    def send_left_click(self, x: int, y: int, delay: float = 0.02, use_post: bool = False):
        """发送鼠标左键点击消息"""
        self.send_left_down(x, y, use_post)
        time.sleep(delay)
        self.send_left_up(x, y, use_post)

    def send_right_down(self, x: int, y: int, use_post: bool = False):
        """发送鼠标右键按下消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(x, y)

        if use_post:
            PostMessage(self.hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
        else:
            SendMessage(self.hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)

    def send_right_up(self, x: int, y: int, use_post: bool = False):
        """发送鼠标右键释放消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(x, y)

        if use_post:
            PostMessage(self.hwnd, WM_RBUTTONUP, 0, lparam)
        else:
            SendMessage(self.hwnd, WM_RBUTTONUP, 0, lparam)

    def send_right_click(self, x: int, y: int, delay: float = 0.02, use_post: bool = False):
        """发送鼠标右键点击消息"""
        self.send_right_down(x, y, use_post)
        time.sleep(delay)
        self.send_right_up(x, y, use_post)

    def send_middle_down(self, x: int, y: int, use_post: bool = False):
        """发送鼠标中键按下消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(x, y)

        if use_post:
            PostMessage(self.hwnd, WM_MBUTTONDOWN, MK_MBUTTON, lparam)
        else:
            SendMessage(self.hwnd, WM_MBUTTONDOWN, MK_MBUTTON, lparam)

    def send_middle_up(self, x: int, y: int, use_post: bool = False):
        """发送鼠标中键释放消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(x, y)

        if use_post:
            PostMessage(self.hwnd, WM_MBUTTONUP, 0, lparam)
        else:
            SendMessage(self.hwnd, WM_MBUTTONUP, 0, lparam)

    def send_middle_click(self, x: int, y: int, delay: float = 0.02, use_post: bool = False):
        """发送鼠标中键点击消息"""
        self.send_middle_down(x, y, use_post)
        time.sleep(delay)
        self.send_middle_up(x, y, use_post)

    def send_mouse_wheel(self, delta: int, use_post: bool = False):
        """发送鼠标滚轮消息（正值向上，负值向下）"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = MAKELPARAM(0, 0)
        wparam = delta << 16

        if use_post:
            PostMessage(self.hwnd, WM_MOUSEWHEEL, wparam, lparam)
        else:
            SendMessage(self.hwnd, WM_MOUSEWHEEL, wparam, lparam)

