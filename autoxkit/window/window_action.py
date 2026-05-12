import time
import ctypes
from ctypes import wintypes
from ..constants import Hex_Key_Code as HKC
from ..mousekey import KeyBoard, Mouse

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

# 定义窗口激活消息常量
WM_ACTIVATE = 0x0006
WA_ACTIVE = 1

# 定义坐标转换宏
MAKELPARAM = lambda x, y: (y << 16) | (x & 0xFFFF)  # noqa: E731


class WindowAction:
    """
        窗口操作类
    Args:
        hwnd (int): 窗口句柄
    """
    def __init__(self, hwnd: int = None):
        self.hwnd = hwnd if hwnd else None
        self.key_board = KeyBoard()
        self.mouse = Mouse()

        self.mouse_point = tuple()
        self.mouse_state = 0
        self.button_mapping = {
            0: [WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON],
            1: [WM_RBUTTONDOWN, WM_RBUTTONUP, MK_RBUTTON],
            2: [WM_MBUTTONDOWN, WM_MBUTTONUP, MK_MBUTTON],
        }

        # 窗口客户区位置
        self.client_point = wintypes.POINT(0, 0)
        ctypes.windll.user32.ClientToScreen(self.hwnd, ctypes.byref(self.client_point))

        self.global_key = False
        self.global_mouse = False

    def send_activate_message(self, mode='send'):
        """
            发送虚拟激活消息，让窗口认为自己被激活
        Args:
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        if mode == 'post':
            PostMessage(self.hwnd, WM_ACTIVATE, WA_ACTIVE, 0)
        elif mode == 'send' or mode == 'global':
            SendMessage(self.hwnd, WM_ACTIVATE, WA_ACTIVE, 0)
        else:
            raise ValueError("Invalid mode. Must be 'send', 'post', or 'global'.")
        time.sleep(0.02)  # 等待窗口处理激活消息

    def send_key_down(self, key_name: str, mode='send'):
        """
            发送按键按下消息
        Args:
            key_name (str): 按键名称
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        if mode == 'global':
            self.key_board.key_down(key_name)
            return

        vk = HKC[key_name]
        scan = MapVirtualKey(vk, 0)
        lparam = (scan << 16) | 1
        if mode == 'post':
            self.send_activate_message(mode)
            PostMessage(self.hwnd, WM_KEYDOWN, vk, lparam)
        elif mode == 'send':
            self.send_activate_message(mode)
            SendMessage(self.hwnd, WM_KEYDOWN, vk, lparam)
        else:
            raise ValueError("Invalid mode. Must be 'send', 'post', or 'global'.")

    def send_key_up(self, key_name: str, mode='send'):
        """
            发送按键释放消息
        Args:
            key_name (str): 按键名称
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        if mode == 'global':
            self.key_board.key_up(key_name)
            return

        vk = HKC[key_name]
        scan = MapVirtualKey(vk, 0)
        lparam = (scan << 16) | 0xC0000001
        if mode == 'post':
            self.send_activate_message(mode)
            PostMessage(self.hwnd, WM_KEYUP, vk, lparam)
        elif mode == 'send':
            self.send_activate_message(mode)
            SendMessage(self.hwnd, WM_KEYUP, vk, lparam)
        else:
            raise ValueError("Invalid mode. Must be 'send', 'post', or 'global'.")

    def send_key_click(self, key_name: str, delay: float = 0.02, mode='send'):
        """
            发送按键点击消息
        Args:
            key_name (str): 按键名称
            delay (float): 按键按下和释放之间的延迟时间。默认 0.02
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        self.send_key_down(key_name, mode)
        time.sleep(delay)
        self.send_key_up(key_name, mode)

    def send_key_combination(self, keys: list, mode='send'):
        """
            发送组合键消息
        Args:
            keys (list): 组合键列表，例如 ['Ctrl', 'A']
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        for key in keys:
            self.send_key_down(key, mode)
            time.sleep(0.01)
        time.sleep(0.01)
        for key in reversed(keys):
            self.send_key_up(key, mode)
            time.sleep(0.01)

    def send_text(self, text: str, mode='send'):
        """
            发送文本消息
        Args:
            text (str): 要发送的文本
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        self.send_activate_message(mode)
        for char in text:
            if mode == 'post':
                PostMessage(self.hwnd, WM_CHAR, ord(char), 0)
            elif mode == 'send' or mode == 'global':
                SendMessage(self.hwnd, WM_CHAR, ord(char), 0)
            else:
                raise ValueError("Invalid mode. Must be 'send', 'post', or 'global'.")
            time.sleep(0.02)

    def send_mouse_down(self, x: int=None, y: int=None, button: int = 0, mode='send'):
        """
            发送鼠标按下消息
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            button (int): 鼠标按钮(0:左键, 1:右键, 2:中键)
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        if mode == 'global':
            self.mouse.mouse_down(self.client_point.x + x, self.client_point.y + y, button)
            return

        lparam = self._verify_mouse_point(x, y)
        self.mouse_state |= self.button_mapping[button][2]

        if mode == 'post':
            self.send_activate_message(mode)
            PostMessage(self.hwnd, self.button_mapping[button][0], self.button_mapping[button][2], lparam)
        elif mode == 'send':
            self.send_activate_message(mode)
            SendMessage(self.hwnd, self.button_mapping[button][0], self.button_mapping[button][2], lparam)
        else:
            raise ValueError("Invalid mode. Must be 'send', 'post', or 'global'.")

    def send_mouse_up(self, x: int=None, y: int=None, button: int = 0, mode='send'):
        """
            发送鼠标释放消息
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            button (int): 鼠标按钮(0:左键, 1:右键, 2:中键)
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        if mode == 'global':
            self.mouse.mouse_up(self.client_point.x + x, self.client_point.y + y, button)
            return

        lparam = self._verify_mouse_point(x, y)
        self.mouse_state &= ~self.button_mapping[button][2]

        if mode == 'post':
            self.send_activate_message(mode)
            PostMessage(self.hwnd, self.button_mapping[button][1], 0, lparam)
        elif mode == 'send':
            self.send_activate_message(mode)
            SendMessage(self.hwnd, self.button_mapping[button][1], 0, lparam)
        else:
            raise ValueError("Invalid mode. Must be 'send', 'post', or 'global'.")

    def send_mouse_click(self, x: int=None, y: int=None, button: int = 0, delay: float = 0.02, mode='send'):
        """
            发送鼠标点击消息
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            delay (float): 点击间隔延迟时间(秒)
            button (int): 鼠标按钮(0:左键, 1:右键, 2:中键)
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        self.send_mouse_down(x, y, button, mode)
        time.sleep(delay)
        self.send_mouse_up(x, y, button, mode)

    def send_mouse_move(self, x: int=None, y: int=None, duration: float = 0.2, steps: int = 10, mode='send'):
        """
            发送鼠标移动消息
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            duration (float): 移动总用时(秒)
            steps (int): 移动拆分步数
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        if mode == 'global':
            self.mouse.mouse_move(self.client_point.x + x, self.client_point.y + y, duration, steps)
            return

        # 获取当前鼠标位置（使用记录的位置，如果没有则使用目标位置）
        if self.mouse_point:
            start_x, start_y = self.mouse_point
        else:
            start_x, start_y = x, y

        self.send_activate_message(mode)

        # 如果持续时间为0或步数小于等于1，直接移动到目标位置
        if duration <= 0 or steps <= 1:
            lparam = self._verify_mouse_point(x, y)
            if mode == 'post':
                PostMessage(self.hwnd, WM_MOUSEMOVE, self.mouse_state, lparam)
            elif mode == 'send':
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
            lparam = self._verify_mouse_point(int(current_x), int(current_y))

            # 发送鼠标移动消息
            if mode == 'post':
                PostMessage(self.hwnd, WM_MOUSEMOVE, self.mouse_state, lparam)
            elif mode == 'send':
                SendMessage(self.hwnd, WM_MOUSEMOVE, self.mouse_state, lparam)

            # 等待一段时间
            time.sleep(step_interval)

    def send_mouse_wheel(self, amount: int, x: int=None, y: int=None, mode='send'):
        """
            发送鼠标滚轮消息
        Args:
            amount (int): 滚动距离(正值向上，负值向下)
            mode (str): 发送模式，'send', 'post', 'global'。默认 'send'
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        # 获取当前鼠标位置（使用记录的位置，如果没有则使用窗口中心）
        if x is not None and y is not None:
            x, y = x, y
        elif self.mouse_point:
            x, y = self.mouse_point
        else:
            # 获取窗口矩形
            rect = wintypes.RECT()
            user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
            # 使用窗口中心作为默认位置
            x = (rect.left + rect.right) // 2
            y = (rect.top + rect.bottom) // 2

        if mode == 'global':
            self.mouse.mouse_wheel(self.client_point.x + x, self.client_point.y + y, amount)
            return

        self.send_activate_message(mode)
        # 确保使用屏幕坐标
        lparam = MAKELPARAM(x, y)
        # 高16位是滚轮滚动量，低16位是鼠标状态
        wparam = (amount << 16) | (self.mouse_state & 0xFFFF)

        if mode == 'post':
            PostMessage(self.hwnd, WM_MOUSEWHEEL, wparam, lparam)
        elif mode == 'send':
            SendMessage(self.hwnd, WM_MOUSEWHEEL, wparam, lparam)

    def _verify_mouse_point(self, x: int=None, y: int=None):
        """验证鼠标位置"""
        if x is not None and y is not None:
            lparam = MAKELPARAM(x, y)
            self.mouse_point = (x, y)
            return lparam
        elif self.mouse_point:
            lparam = MAKELPARAM(self.mouse_point[0], self.mouse_point[1])
            return lparam
        raise ValueError("鼠标位置未设置")

