import ctypes
import ctypes.wintypes
import time
from .input import Input_I, Input, MouseInput
from ..constants import Hex_Mouse_Code as HMC

user32 = ctypes.windll.user32
SendInput = user32.SendInput

class Mouse:

    def __init__(self):
        """初始化鼠标控制器"""
        self.mouse_point = tuple()
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)

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

    def left_down(self, x: int=None, y: int=None):
        """鼠标左键按下"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["MLeftDown"])

    def left_up(self, x: int=None, y: int=None):
        """鼠标左键释放"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["MLeftUp"])

    def left_click(self, x: int=None, y: int=None, delay: float=0.02):
        """鼠标左键点击（可设置按下持续时间）"""
        self.left_down(x, y)
        time.sleep(delay)
        self.left_up(x, y)

    def right_down(self, x: int=None, y: int=None):
        """鼠标右键按下"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["MRightDown"])

    def right_up(self, x: int=None, y: int=None):
        """鼠标右键释放"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["MRightUp"])

    def right_click(self, x: int=None, y: int=None, delay: float=0.02):
        """鼠标右键点击（可设置按下持续时间）"""
        self.right_down(x, y)
        time.sleep(delay)
        self.right_up(x, y)

    def middle_down(self, x: int=None, y: int=None):
        """鼠标中键按下"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["MiddleDown"])

    def middle_up(self, x: int=None, y: int=None):
        """鼠标中键释放"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["MiddleUp"])

    def middle_click(self, x: int=None, y: int=None, delay: float=0.02):
        """鼠标中键点击（可设置按下持续时间）"""
        self.middle_down(x, y)
        time.sleep(delay)
        self.middle_up(x, y)

    def side1_down(self, x: int=None, y: int=None):
        """鼠标侧键1（前进键）按下"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["XDown"], data=HMC["side1"])

    def side1_up(self, x: int=None, y: int=None):
        """鼠标侧键1（前进键）释放"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["XUp"], data=HMC["side1"])

    def side1_click(self, x: int=None, y: int=None, delay: float=0.02):
        """鼠标侧键1点击（可设置按下持续时间）"""
        self.side1_down(x, y)
        time.sleep(delay)
        self.side1_up(x, y)

    def side2_down(self, x: int=None, y: int=None):
        """鼠标侧键2（后退键）按下"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["XDown"], data=HMC["side2"])

    def side2_up(self, x: int=None, y: int=None):
        """鼠标侧键2（后退键）释放"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["XUp"], data=HMC["side2"])

    def side2_click(self, x: int=None, y: int=None, delay: float=0.02):
        """鼠标侧键2点击（可设置按下持续时间）"""
        self.side2_down(x, y)
        time.sleep(delay)
        self.side2_up(x, y)

    def wheel_scroll(self, amount: int, x: int=None, y: int=None):
        """垂直滚轮滚动（正值向上，负值向下）"""
        x, y = self._verify_mouse_point(x, y)
        if x is not None and y is not None:
            self.mouse_move(x, y)
        self._mouse_action(HMC["Wheel"], data=amount * 10)

    def mouse_move(self, x: int, y: int, duration: float = 0.2, steps: int = 10):
        """
        绝对移动 | 线性移动；
        x, y: 目标位置坐标(绝对坐标)；
        duration: 移动总用时(秒)；
        steps: 移动拆分步数；
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

    def get_mouse_position(self):
        """获取鼠标位置"""
        point = ctypes.wintypes.POINT()
        if user32.GetCursorPos(ctypes.byref(point)):
            return point.x, point.y
        else:
            raise ctypes.WinError(ctypes.get_last_error())