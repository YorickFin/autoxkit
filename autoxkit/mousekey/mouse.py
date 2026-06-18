import ctypes
import ctypes.wintypes
import time
from .input import Input_I, Input, MouseInput
from ..constants import Hex_Mouse_Code as HMC

user32 = ctypes.windll.user32
point = ctypes.wintypes.POINT()
SendInput = user32.SendInput

class Mouse:

    def __init__(self):
        """初始化鼠标控制器"""
        self.mouse_point = tuple()
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)
        self.button_mapping = {
            0: [HMC["MLeftDown"], HMC["MLeftUp"], 0],
            1: [HMC["MRightDown"], HMC["MRightUp"], 0],
            2: [HMC["MiddleDown"], HMC["MiddleUp"], 0],
            3: [HMC["XDown"], HMC["XUp"], HMC["MSide1"]],
            4: [HMC["XDown"], HMC["XUp"], HMC["MSide2"]],
        }

    def _mouse_action(self, flags, x=0, y=0, data=0):
        """执行鼠标动作的底层函数"""
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(x, y, data, flags, 0, ctypes.pointer(extra))
        input_struct = Input(ctypes.c_ulong(0), ii_)
        SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))

    def _verify_mouse_point(self, x: int=None, y: int=None):
        """验证鼠标坐标是否在屏幕范围内"""
        if x is None or y is None:
            if self.mouse_point:
                x, y = self.mouse_point
            else:
                x, y = None, None
        else:
            self.mouse_point = (x, y)
        return x, y

    def mouse_down(self, x: int=None, y: int=None, button: int=0):
        """
            鼠标按下
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            button (int): 鼠标按钮(0:左键, 1:右键, 2:中键, 3:侧键1, 4:侧键2)
        """
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y, steps=1)
        self._mouse_action(self.button_mapping[button][0], data=self.button_mapping[button][2])

    def mouse_up(self, x: int=None, y: int=None, button: int=0):
        """
            鼠标释放
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            button (int): 鼠标按钮(0:左键, 1:右键, 2:中键, 3:侧键1, 4:侧键2)
        """
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y, steps=1)
        self._mouse_action(self.button_mapping[button][1], data=self.button_mapping[button][2])

    def mouse_click(self, x: int=None, y: int=None, button: int=0, delay: float=0.02):
        """
            鼠标点击
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            button (int): 鼠标按钮(0:左键, 1:右键, 2:中键, 3:侧键1, 4:侧键2)
            delay (float): 点击间隔延迟时间（秒）
        """
        self.mouse_down(x, y, button)
        time.sleep(delay)
        self.mouse_up(x, y, button)

    def mouse_move(self, x: int, y: int, duration: float = 0.2, steps: int = 10):
        """
            绝对移动 | 线性移动
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            duration (float): 移动总用时(秒)
            steps (int): 移动拆分步数
        """
        x, y = self._verify_mouse_point(x, y)
        start_x, start_y = self.get_mouse_position()

        if duration <= 0 or steps <= 1:
            abs_x = int((x / self.screen_width) * 65535)
            abs_y = int((y / self.screen_height) * 65535)
            self._mouse_action(HMC["Move"] | 0x8000, x=abs_x, y=abs_y)
            return

        step_interval = duration / steps

        for i in range(1, steps + 1):
            t = i / steps

            current_x = start_x + (x - start_x) * t
            current_y = start_y + (y - start_y) * t

            abs_x = int((current_x / self.screen_width) * 65535)
            abs_y = int((current_y / self.screen_height) * 65535)

            self._mouse_action(HMC["Move"] | 0x8000, x=abs_x, y=abs_y)

            time.sleep(step_interval)

    def mouse_wheel(self, distance: int, x: int=None, y: int=None):
        """
            垂直滚轮滚动
        Args:
            x (int): 目标X坐标
            y (int): 目标Y坐标
            distance (int): 滚动距离(正值向上，负值向下)
        """
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y, steps=1)
        self._mouse_action(HMC["Wheel"], data=distance * 120)

    def get_mouse_position(self):
        """
            获取鼠标位置
        Returns:
            tuple[int, int]: 鼠标当前位置的 (X, Y) 坐标
        """
        if user32.GetCursorPos(ctypes.byref(point)):
            return point.x, point.y
        else:
            raise ctypes.WinError(ctypes.get_last_error())