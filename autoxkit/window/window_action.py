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

# 获取窗口矩形
GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
GetWindowRect.restype = wintypes.BOOL

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
    """
    窗口操作类
    Args:
        hwnd (int): 窗口句柄
        mouse_point (tuple): 记录鼠标当前位置
        mouse_state (int): 记录鼠标按键状态
    """
    def __init__(self, hwnd: int = None):
        self.hwnd = hwnd if hwnd else None
        self.mouse_point = tuple()
        self.mouse_state = 0

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
            time.sleep(0.02)

    def send_mouse_move(self, x: int=None, y: int=None, duration: float = 0.2, steps: int = 10, use_post: bool = False):
        """发送鼠标移动消息

        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动总用时(秒)
            steps: 移动拆分步数
            use_post: 是否使用PostMessage
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        # 获取当前鼠标位置（使用记录的位置，如果没有则使用目标位置）
        if self.mouse_point:
            start_x, start_y = self.mouse_point
        else:
            start_x, start_y = x, y

        # 如果持续时间为0或步数小于等于1，直接移动到目标位置
        if duration <= 0 or steps <= 1:
            lparam = self.verify_mouse_point(x, y)
            if use_post:
                PostMessage(self.hwnd, WM_MOUSEMOVE, self.mouse_state, lparam)
            else:
                SendMessage(self.hwnd, WM_MOUSEMOVE, self.mouse_state, lparam)
            return

        # 计算每步的时间间隔
        step_interval = duration / steps

        # 执行平滑移动
        for i in range(1, steps + 1):
            # 计算当前步的插值比例
            t = i / steps

            # 计算当前步的坐标
            current_x = start_x + (x - start_x) * t
            current_y = start_y + (y - start_y) * t

            # 创建消息参数
            lparam = self.verify_mouse_point(int(current_x), int(current_y))

            # 发送鼠标移动消息
            if use_post:
                PostMessage(self.hwnd, WM_MOUSEMOVE, self.mouse_state, lparam)
            else:
                SendMessage(self.hwnd, WM_MOUSEMOVE, self.mouse_state, lparam)

            # 等待一段时间
            time.sleep(step_interval)

    def send_left_down(self, x: int=None, y: int=None, use_post: bool = False):
        """发送鼠标左键按下消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = self.verify_mouse_point(x, y)
        self.mouse_state |= MK_LBUTTON

        if use_post:
            PostMessage(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        else:
            SendMessage(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)

    def send_left_up(self, x: int=None, y: int=None, use_post: bool = False):
        """发送鼠标左键释放消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = self.verify_mouse_point(x, y)
        self.mouse_state &= ~MK_LBUTTON

        if use_post:
            PostMessage(self.hwnd, WM_LBUTTONUP, 0, lparam)
        else:
            SendMessage(self.hwnd, WM_LBUTTONUP, 0, lparam)

    def send_left_click(self, x: int=None, y: int=None, delay: float = 0.02, use_post: bool = False):
        """发送鼠标左键点击消息"""
        self.send_left_down(x, y, use_post)
        time.sleep(delay)
        self.send_left_up(x, y, use_post)

    def send_right_down(self, x: int=None, y: int=None, use_post: bool = False):
        """发送鼠标右键按下消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = self.verify_mouse_point(x, y)
        self.mouse_state |= MK_RBUTTON

        if use_post:
            PostMessage(self.hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
        else:
            SendMessage(self.hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)

    def send_right_up(self, x: int=None, y: int=None, use_post: bool = False):
        """发送鼠标右键释放消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = self.verify_mouse_point(x, y)
        self.mouse_state &= ~MK_RBUTTON

        if use_post:
            PostMessage(self.hwnd, WM_RBUTTONUP, 0, lparam)
        else:
            SendMessage(self.hwnd, WM_RBUTTONUP, 0, lparam)

    def send_right_click(self, x: int=None, y: int=None, delay: float = 0.02, use_post: bool = False):
        """发送鼠标右键点击消息"""
        self.send_right_down(x, y, use_post)
        time.sleep(delay)
        self.send_right_up(x, y, use_post)

    def send_middle_down(self, x: int=None, y: int=None, use_post: bool = False):
        """发送鼠标中键按下消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = self.verify_mouse_point(x, y)
        self.mouse_state |= MK_MBUTTON

        if use_post:
            PostMessage(self.hwnd, WM_MBUTTONDOWN, MK_MBUTTON, lparam)
        else:
            SendMessage(self.hwnd, WM_MBUTTONDOWN, MK_MBUTTON, lparam)

    def send_middle_up(self, x: int=None, y: int=None, use_post: bool = False):
        """发送鼠标中键释放消息"""
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        lparam = self.verify_mouse_point(x, y)
        self.mouse_state &= ~MK_MBUTTON

        if use_post:
            PostMessage(self.hwnd, WM_MBUTTONUP, 0, lparam)
        else:
            SendMessage(self.hwnd, WM_MBUTTONUP, 0, lparam)

    def send_middle_click(self, x: int=None, y: int=None, delay: float = 0.02, use_post: bool = False):
        """发送鼠标中键点击消息"""
        self.send_middle_down(x, y, use_post)
        time.sleep(delay)
        self.send_middle_up(x, y, use_post)

    def send_mouse_wheel(self, delta: int, use_post: bool = False):
        """发送鼠标滚轮消息（正值向上，负值向下）

        Args:
            delta: 滚动值（正值向上，负值向下）
            use_post: 是否使用PostMessage
            activate_window: 是否在发送消息前激活窗口
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        # 获取当前鼠标位置（使用记录的位置，如果没有则使用窗口中心）
        if self.mouse_point:
            x, y = self.mouse_point
        else:
            # 获取窗口矩形
            rect = wintypes.RECT()
            user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
            # 使用窗口中心作为默认位置
            x = (rect.left + rect.right) // 2
            y = (rect.top + rect.bottom) // 2

        # 确保使用屏幕坐标
        lparam = MAKELPARAM(x, y)
        # 高16位是滚轮滚动量，低16位是鼠标状态
        wparam = (delta << 16) | (self.mouse_state & 0xFFFF)

        if use_post:
            PostMessage(self.hwnd, WM_MOUSEWHEEL, wparam, lparam)
        else:
            SendMessage(self.hwnd, WM_MOUSEWHEEL, wparam, lparam)

    def verify_mouse_point(self, x: int=None, y: int=None):
        """验证鼠标位置"""
        if x is not None and y is not None:
            lparam = MAKELPARAM(x, y)
            self.mouse_point = (x, y)
            return lparam
        elif self.mouse_point:
            lparam = MAKELPARAM(self.mouse_point[0], self.mouse_point[1])
            return lparam
