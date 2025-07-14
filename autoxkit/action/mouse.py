import ctypes
import time

# 定义常量
MOUSEEVENTF_MOVE       = 0x0001
MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040
MOUSEEVENTF_XDOWN      = 0x0080
MOUSEEVENTF_XUP        = 0x0100
MOUSEEVENTF_WHEEL      = 0x0800
MOUSEEVENTF_HWHEEL     = 0x1000
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

# 定义结构体
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("_input", _INPUT)
    ]

# 设置SendInput函数
SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = ctypes.c_uint

def mouse_action(flags, x=0, y=0, data=0):
    """执行鼠标动作的底层函数"""
    extra = ctypes.c_ulong(0)
    mouse_input = MOUSEINPUT(
        dx=x,
        dy=y,
        mouseData=data,
        dwFlags=flags,
        time=0,
        dwExtraInfo=ctypes.pointer(extra)
    )

    input_struct = INPUT(
        type=0,  # INPUT_MOUSE
        _input=INPUT._INPUT(mi=mouse_input)
    )

    SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(INPUT))

# ===== 封装鼠标操作函数 =====

def left_down():
    """鼠标左键按下"""
    mouse_action(MOUSEEVENTF_LEFTDOWN)

def left_up():
    """鼠标左键释放"""
    mouse_action(MOUSEEVENTF_LEFTUP)

def left_click(delay=0.04):
    """鼠标左键点击（可设置按下持续时间）"""
    left_down()
    time.sleep(delay)
    left_up()

def right_down():
    """鼠标右键按下"""
    mouse_action(MOUSEEVENTF_RIGHTDOWN)

def right_up():
    """鼠标右键释放"""
    mouse_action(MOUSEEVENTF_RIGHTUP)

def right_click(delay=0.04):
    """鼠标右键点击（可设置按下持续时间）"""
    right_down()
    time.sleep(delay)
    right_up()

def side1_down():
    """鼠标侧键1（前进键）按下"""
    mouse_action(MOUSEEVENTF_XDOWN, data=XBUTTON1)

def side1_up():
    """鼠标侧键1（前进键）释放"""
    mouse_action(MOUSEEVENTF_XUP, data=XBUTTON1)

def side1_click(delay=0.04):
    """鼠标侧键1点击（可设置按下持续时间）"""
    side1_down()
    time.sleep(delay)
    side1_up()

def side2_down():
    """鼠标侧键2（后退键）按下"""
    mouse_action(MOUSEEVENTF_XDOWN, data=XBUTTON2)

def side2_up():
    """鼠标侧键2（后退键）释放"""
    mouse_action(MOUSEEVENTF_XUP, data=XBUTTON2)

def side2_click(delay=0.04):
    """鼠标侧键2点击（可设置按下持续时间）"""
    side2_down()
    time.sleep(delay)
    side2_up()

def move_relative(dx: int, dy: int):
    """相对移动，相对当前鼠标位置，值：± int"""
    mouse_action(MOUSEEVENTF_MOVE, x=dx, y=dy)

def move_absolute(x: int, y: int):
    """绝对移动鼠标到屏幕坐标"""
    # 将坐标转换为0-65535范围内的绝对坐标
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    abs_x = int((x / screen_width) * 65535)
    abs_y = int((y / screen_height) * 65535)
    mouse_action(MOUSEEVENTF_MOVE | 0x8000, x=abs_x, y=abs_y)

def wheel_scroll(amount: int):
    """垂直滚轮滚动（正数向上，负数向下）"""
    mouse_action(MOUSEEVENTF_WHEEL, data=amount*10)
