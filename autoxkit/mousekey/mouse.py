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
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)

    def _mouse_action(self, flags, x=0, y=0, data=0):
        """执行鼠标动作的底层函数"""
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(x, y, data, flags, 0, ctypes.pointer(extra))
        input_struct = Input(ctypes.c_ulong(0), ii_)
        SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))

    def left_down(self):
        """鼠标左键按下"""
        self._mouse_action(HMC["LeftDown"])

    def left_up(self):
        """鼠标左键释放"""
        self._mouse_action(HMC["LeftUp"])

    def left_click(self, delay: float=0.02):
        """鼠标左键点击（可设置按下持续时间）"""
        self.left_down()
        time.sleep(delay)
        self.left_up()

    def right_down(self):
        """鼠标右键按下"""
        self._mouse_action(HMC["RightDown"])

    def right_up(self):
        """鼠标右键释放"""
        self._mouse_action(HMC["RightUp"])

    def right_click(self, delay: float=0.02):
        """鼠标右键点击（可设置按下持续时间）"""
        self.right_down()
        time.sleep(delay)
        self.right_up()

    def middle_down(self):
        """鼠标中键按下"""
        self._mouse_action(HMC["MiddleDown"])

    def middle_up(self):
        """鼠标中键释放"""
        self._mouse_action(HMC["MiddleUp"])

    def middle_click(self, delay: float=0.02):
        """鼠标中键点击（可设置按下持续时间）"""
        self.middle_down()
        time.sleep(delay)
        self.middle_up()

    def side1_down(self):
        """鼠标侧键1（前进键）按下"""
        self._mouse_action(HMC["XDown"], data=HMC["XButton1"])

    def side1_up(self):
        """鼠标侧键1（前进键）释放"""
        self._mouse_action(HMC["XUp"], data=HMC["XButton1"])

    def side1_click(self, delay: float=0.02):
        """鼠标侧键1点击（可设置按下持续时间）"""
        self.side1_down()
        time.sleep(delay)
        self.side1_up()

    def side2_down(self):
        """鼠标侧键2（后退键）按下"""
        self._mouse_action(HMC["XDown"], data=HMC["XButton2"])

    def side2_up(self):
        """鼠标侧键2（后退键）释放"""
        self._mouse_action(HMC["XUp"], data=HMC["XButton2"])

    def side2_click(self, delay: float=0.02):
        """鼠标侧键2点击（可设置按下持续时间）"""
        self.side2_down()
        time.sleep(delay)
        self.side2_up()

    def wheel_scroll(self, amount: int):
        """垂直滚轮滚动（正值向上，负值向下）"""
        self._mouse_action(HMC["Wheel"], data=amount * 10)

    def mouse_move(self, x: int, y: int, duration: float = 0.2, steps: int = 10):
        """
        绝对移动 | 线性移动；
        x, y: 目标位置坐标(绝对坐标)；
        duration: 移动总用时(秒)；
        steps: 移动拆分步数；
        """
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