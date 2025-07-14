
import ctypes
from ctypes import wintypes, Structure, POINTER, CFUNCTYPE, byref
import time
import threading

running = False

# 键盘按键码
Hex_key_code = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46, "G": 0x47,
    "H": 0x48, "I": 0x49, "J": 0x4a, "K": 0x4b, "L": 0x4c, "M": 0x4d, "N": 0x4e,
    "O": 0x4f, "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54, "U": 0x55,
    "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59, "Z": 0x5a, "Space": 0x20,
    "Oem_4": 0xdb, "Oem_6": 0xdd, "Oem_1": 0xba, "Oem_7": 0xde, "Oem_Comma": 0xbc,
    "Oem_Period": 0xbe, "Oem_2": 0xbf, "Oem_5": 0xdc, "Oem_3": 0xc0, "0": 0x30,
    "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34, "5": 0x35, "6": 0x36, "7": 0x37,
    "8": 0x38, "9": 0x39, "Oem_Minus": 0xbd, "Oem_Plus": 0xbb, "Numpad0": 0x60,
    "Numpad1": 0x61, "Numpad2": 0x62, "Numpad3": 0x63, "Numpad4": 0x64, "Numpad5": 0x65,
    "Numpad6": 0x66, "Numpad7": 0x67, "Numpad8": 0x68, "Numpad9": 0x69, "Decimal": 0x6e,
    "Add": 0x6b, "Subtract": 0x6d, "Multiply": 0x6a, "Divide": 0x6f, "Numlock": 0x90,
    "Return": 0x0D, "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74,
    "F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A,
    "F12": 0x7B, "Back": 0x08, "Tab": 0x09, "Lshift": 0xA0, "Rshift": 0xA1,
    "Lctrl": 0xA2, "Rctrl": 0xA3, "Capital": 0x14, "Lalt": 0xA4, "Ralt": 0xA5,
    "Lwin": 0x5B, "Rwin": 0x5C, "Apps": 0x5D, "Escape": 0x1B, "Insert": 0x2D,
    "Delete": 0x2E, "Home": 0x24, "End": 0x23, "Prior": 0x21, "Next": 0x22,
    "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28, "Volume_Down": 0xAE,
    "Volume_Up": 0xAF, "Volume_Mute": 0xAD, "Launch_App2": 0xB7,
}

# 事件对象定义
class KeyEvent:
    def __init__(self, vk_code):
        self.key_code = vk_code
        name = next((k for k, v in Hex_key_code.items() if v == vk_code), None)
        self.key_name = name if name else str(vk_code)

class MouseEvent:
    def __init__(self, button, x, y):
        self.button = button
        self.position = (x, y)

# 常量定义
WH_KEYBOARD_LL = 13
WH_MOUSE_LL    = 14
WM_KEYDOWN    = 0x0100
WM_KEYUP      = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP   = 0x0105
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP   = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP   = 0x0208
WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP   = 0x020C
XBUTTON1       = 0x0001
XBUTTON2       = 0x0002
PM_REMOVE      = 0x0001

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
_on_keydown = lambda event: None
_on_keyup = lambda event: None
_on_mousedown = lambda event: None
_on_mouseup = lambda event: None

# 设置回调接口
def set_event_handlers(on_keydown=None, on_keyup=None, on_mousedown=None, on_mouseup=None):
    global _on_keydown, _on_keyup, _on_mousedown, _on_mouseup
    if on_keydown:   _on_keydown = on_keydown
    if on_keyup:     _on_keyup   = on_keyup
    if on_mousedown: _on_mousedown = on_mousedown
    if on_mouseup:   _on_mouseup   = on_mouseup

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
        event = KeyEvent(kbd.vkCode)
        if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN): _on_keydown(event)
        elif wParam in (WM_KEYUP, WM_SYSKEYUP):   _on_keyup(event)
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

@HOOKPROC
def mouse_proc(nCode, wParam, lParam):
    if nCode >= 0:
        ms = ctypes.cast(lParam, POINTER(MSLLHOOKSTRUCT)).contents
        x, y = ms.pt.x, ms.pt.y
        if wParam == WM_LBUTTONDOWN:   event = MouseEvent('L', x, y); _on_mousedown(event)
        elif wParam == WM_LBUTTONUP:   event = MouseEvent('L', x, y); _on_mouseup(event)
        elif wParam == WM_RBUTTONDOWN: event = MouseEvent('R', x, y); _on_mousedown(event)
        elif wParam == WM_RBUTTONUP:   event = MouseEvent('R', x, y); _on_mouseup(event)
        elif wParam == WM_MBUTTONDOWN: event = MouseEvent('M', x, y); _on_mousedown(event)
        elif wParam == WM_MBUTTONUP:   event = MouseEvent('M', x, y); _on_mouseup(event)
        elif wParam in (WM_XBUTTONDOWN, WM_XBUTTONUP):
            high = (ms.mouseData >> 16) & 0xFFFF
            btn = 'X1' if high == XBUTTON1 else 'X2'
            event = MouseEvent(btn, x, y)
            if wParam == WM_XBUTTONDOWN: _on_mousedown(event)
            else:                        _on_mouseup(event)
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

# 线程与钩子管理
def start_listening():
    global running, hook_thread
    if running: return
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
    keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_proc, hMod, 0)
    mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_proc, hMod, 0)
    msg = wintypes.MSG()
    while running:
        if user32.PeekMessageW(byref(msg), 0, 0, 0, PM_REMOVE):
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))
        else:
            time.sleep(0.01)