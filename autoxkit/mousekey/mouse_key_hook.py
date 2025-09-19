
import ctypes
from ctypes import wintypes, Structure, POINTER, CFUNCTYPE, byref
import time
import threading
from .constants import Hex_Key_Code, Hex_Hook_Code

HKC = Hex_Key_Code
HHC = Hex_Hook_Code
running = False

# 事件对象定义
class KeyEvent:
    def __init__(self, action, vk_code):
        self.action = action
        self.key_code = vk_code
        name = next((k for k, v in HKC.items() if v == vk_code), None)
        self.key_name = name if name else str(vk_code)

class MouseEvent:
    def __init__(self, action, button, x, y):
        self.action = action
        self.button = button
        self.position = (x, y)

# 钩子回调类型
HOOKPROC = CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# 结构体定义
class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]
class MSLLHOOKSTRUCT(Structure):
    _fields_ = [("pt", wintypes.POINT), ("mouseData", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]

# 加载 DLL
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
# 钩子相关函数签名
user32.SetWindowsHookExW.argtypes = [wintypes.INT, HOOKPROC, ctypes.c_void_p, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_long
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
# 获取模块句柄签名
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
# 获取光标位置签名
user32.GetCursorPos.argtypes = [POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

# 默认事件处理回调
_on_keydown = lambda event: None  # noqa: E731
_on_keyup = lambda event: None  # noqa: E731
_on_mousedown = lambda event: None  # noqa: E731
_on_mouseup = lambda event: None  # noqa: E731

# 设置回调接口
def set_event_handlers(on_keydown=None, on_keyup=None, on_mousedown=None, on_mouseup=None):
    global _on_keydown, _on_keyup, _on_mousedown, _on_mouseup

    if on_keydown:
        _on_keydown = on_keydown
    if on_keyup:
        _on_keyup = on_keyup
    if on_mousedown:
        _on_mousedown = on_mousedown
    if on_mouseup:
        _on_mouseup = on_mouseup

# 获取当前鼠标位置
def get_mouse_position():
    pt = wintypes.POINT()
    if user32.GetCursorPos(byref(pt)):
        return (pt.x, pt.y)
    return (None, None)

@HOOKPROC
def keyboard_proc(nCode, wParam, lParam):
    if nCode >= 0:
        kbd = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
        if wParam in (HHC["KeyDown"], HHC["SysKeyDown"]):
            event = KeyEvent('KeyDown', kbd.vkCode)
            _on_keydown(event)
        elif wParam in (HHC["KeyUp"], HHC["SysKeyUp"]):
            event = KeyEvent('KeyUp', kbd.vkCode)
            _on_keyup(event)
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

@HOOKPROC
def mouse_proc(nCode, wParam, lParam):
    if nCode >= 0:
        ms = ctypes.cast(lParam, POINTER(MSLLHOOKSTRUCT)).contents
        x, y = ms.pt.x, ms.pt.y
        if wParam == HHC["LeftDown"]:
            event = MouseEvent('MouseDown', 'Left', x, y)
            _on_mousedown(event)
        elif wParam == HHC["LeftUp"]:
            event = MouseEvent('MouseUp', 'Left', x, y)
            _on_mouseup(event)
        elif wParam == HHC["RightDown"]:
            event = MouseEvent('MouseDown', 'Right', x, y)
            _on_mousedown(event)
        elif wParam == HHC["RightUp"]:
            event = MouseEvent('MouseUp', 'Right', x, y)
            _on_mouseup(event)
        elif wParam == HHC["MiddleDown"]:
            event = MouseEvent('MouseDown', 'Middle', x, y)
            _on_mousedown(event)
        elif wParam == HHC["MiddleUp"]:
            event = MouseEvent('MouseUp', 'Middle', x, y)
            _on_mouseup(event)
        elif wParam in (HHC["XDown"], HHC["XUp"]):
            high = (ms.mouseData >> 16) & 0xFFFF
            btn = 'XButton1' if high == HHC["XButton1"] else 'XButton2'
            if wParam == HHC["XDown"]:
                event = MouseEvent('MouseDown', btn, x, y)
                _on_mousedown(event)
            else:
                event = MouseEvent('MouseUp', btn, x, y)
                _on_mouseup(event)
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

# 线程与钩子管理
def start_listening():
    global running, hook_thread
    if running:
        return
    running = True
    hook_thread = threading.Thread(target=_thread_func, daemon=True)
    hook_thread.start()

def stop_listening():
    global running
    running = False

def _thread_func():
    global keyboard_hook, mouse_hook, thread_id
    thread_id = kernel32.GetCurrentThreadId()
    hMod = kernel32.GetModuleHandleW(None)
    keyboard_hook = user32.SetWindowsHookExW(HHC["Key_LL"], keyboard_proc, hMod, 0)
    mouse_hook = user32.SetWindowsHookExW(HHC["Mouse_LL"], mouse_proc, hMod, 0)
    msg = wintypes.MSG()
    while running:
        if user32.PeekMessageW(byref(msg), 0, 0, 0, HHC["PM_REMOVE"]):
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))
        else:
            time.sleep(0.01)