# hook_impl.py
import ctypes
from ctypes import wintypes, Structure, POINTER, CFUNCTYPE, byref
import time
import threading
from .constants import Hex_Key_Code, Hex_Hook_Code

HKC = Hex_Key_Code
HHC = Hex_Hook_Code

# ---------- 结构体定义 ----------
class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class MSLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

# ---------- 事件对象 ----------
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

# ---------- 回调类型 ----------
HOOKPROC = CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# ---------- 加载 DLL 并声明 API 签名（你指出必须有的部分） ----------
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# SetWindowsHookExW
user32.SetWindowsHookExW.argtypes = [wintypes.INT, HOOKPROC, ctypes.c_void_p, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK

# CallNextHookEx
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_long

# UnhookWindowsHookEx
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL

# GetModuleHandleW
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

# GetCursorPos
user32.GetCursorPos.argtypes = [POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

# Message functions used in the pump loop
user32.PeekMessageW.argtypes = [POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
user32.PeekMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [POINTER(wintypes.MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = ctypes.c_long

# ---------- HookListener 类 ----------
class HookListener:
    """
    每个实例可以独立运行、独立添加多个回调（keydown/keyup/mousedown/mouseup）。
    使用示例见文件末尾。
    """
    def __init__(self):
        # 回调列表（支持多个回调）
        self._on_keydown = []
        self._on_keyup = []
        self._on_mousedown = []
        self._on_mouseup = []

        # 钩子与线程状态
        self.running = False
        self._thread = None
        self.keyboard_hook = None
        self.mouse_hook = None

        # 必须保存CFUNCTYPE对象引用，避免被GC回收
        # 绑定到实例的 method（bound method）是合法的 callable
        self._keyboard_proc_c = HOOKPROC(self._keyboard_proc)
        self._mouse_proc_c = HOOKPROC(self._mouse_proc)

        # module handles
        self._hMod = kernel32.GetModuleHandleW(None)

    # 注册回调
    def add_handler(self, event_type: str, func):
        if event_type == "keydown":
            self._on_keydown.append(func)
        elif event_type == "keyup":
            self._on_keyup.append(func)
        elif event_type == "mousedown":
            self._on_mousedown.append(func)
        elif event_type == "mouseup":
            self._on_mouseup.append(func)
        else:
            raise ValueError("unknown event_type: " + str(event_type))

    # 移除回调（可选）
    def remove_handler(self, event_type: str, func):
        target = None
        if event_type == "keydown":
            target = self._on_keydown
        elif event_type == "keyup":
            target = self._on_keyup
        elif event_type == "mousedown":
            target = self._on_mousedown
        elif event_type == "mouseup":
            target = self._on_mouseup
        else:
            raise ValueError("unknown event_type: " + str(event_type))
        try:
            target.remove(func)
        except ValueError:
            raise ValueError("function not found: " + str(func))

    # 获取当前鼠标位置
    def get_mouse_position(self):
        pt = wintypes.POINT()
        if user32.GetCursorPos(byref(pt)):
            return (pt.x, pt.y)
        else:
            raise ctypes.WinError(ctypes.get_last_error())

    # 内部键盘回调（bound method -> can be wrapped by CFUNCTYPE）
    def _keyboard_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            kbd = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
            if wParam in (HHC["KeyDown"], HHC["SysKeyDown"]):
                event = KeyEvent('KeyDown', kbd.vkCode)
                for cb in list(self._on_keydown):
                    try:
                        cb(event)
                    except Exception:
                        # 回调异常不应终止钩子链
                        pass
            elif wParam in (HHC["KeyUp"], HHC["SysKeyUp"]):
                event = KeyEvent('KeyUp', kbd.vkCode)
                for cb in list(self._on_keyup):
                    try:
                        cb(event)
                    except Exception:
                        pass
        # 注意：第一个参数应传入 hook handle 或 None（对 LL hook 可为 None）
        return user32.CallNextHookEx(self.keyboard_hook, nCode, wParam, lParam)

    # 内部鼠标回调
    def _mouse_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            ms = ctypes.cast(lParam, POINTER(MSLLHOOKSTRUCT)).contents
            x, y = ms.pt.x, ms.pt.y
            try:
                if wParam == HHC["LeftDown"]:
                    event = MouseEvent('MouseDown', 'Left', x, y)
                    for cb in list(self._on_mousedown):
                        cb(event)
                elif wParam == HHC["LeftUp"]:
                    event = MouseEvent('MouseUp', 'Left', x, y)
                    for cb in list(self._on_mouseup):
                        cb(event)
                elif wParam == HHC["RightDown"]:
                    event = MouseEvent('MouseDown', 'Right', x, y)
                    for cb in list(self._on_mousedown):
                        cb(event)
                elif wParam == HHC["RightUp"]:
                    event = MouseEvent('MouseUp', 'Right', x, y)
                    for cb in list(self._on_mouseup):
                        cb(event)
                elif wParam == HHC["MiddleDown"]:
                    event = MouseEvent('MouseDown', 'Middle', x, y)
                    for cb in list(self._on_mousedown):
                        cb(event)
                elif wParam == HHC["MiddleUp"]:
                    event = MouseEvent('MouseUp', 'Middle', x, y)
                    for cb in list(self._on_mouseup):
                        cb(event)
                elif wParam in (HHC["XDown"], HHC["XUp"]):
                    high = (ms.mouseData >> 16) & 0xFFFF
                    btn = 'XButton1' if high == HHC["XButton1"] else 'XButton2'
                    if wParam == HHC["XDown"]:
                        event = MouseEvent('MouseDown', btn, x, y)
                        for cb in list(self._on_mousedown):
                            cb(event)
                    else:
                        event = MouseEvent('MouseUp', btn, x, y)
                        for cb in list(self._on_mouseup):
                            cb(event)
            except Exception:
                # 忽略回调异常
                pass
        return user32.CallNextHookEx(self.mouse_hook, nCode, wParam, lParam)

    # 启动监听（新线程 pump message loop）
    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._thread_func, daemon=True)
        self._thread.start()

    # 停止监听并取消钩子
    def stop(self):
        self.running = False
        # 等待线程退出并且取消钩子
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        # 尝试取消钩子（若尚未取消）
        if self.keyboard_hook:
            try:
                user32.UnhookWindowsHookEx(self.keyboard_hook)
            except Exception:
                pass
            self.keyboard_hook = None
        if self.mouse_hook:
            try:
                user32.UnhookWindowsHookEx(self.mouse_hook)
            except Exception:
                pass
            self.mouse_hook = None

    # 线程体：注册钩子并 pump 消息
    def _thread_func(self):
        try:
            # 注册钩子（低级钩子一般可以传 module handle + threadId=0）
            self.keyboard_hook = user32.SetWindowsHookExW(HHC["Key_LL"], self._keyboard_proc_c, self._hMod, 0)
            self.mouse_hook = user32.SetWindowsHookExW(HHC["Mouse_LL"], self._mouse_proc_c, self._hMod, 0)
        except Exception:
            # 若注册失败，结束
            self.running = False
            return

        msg = wintypes.MSG()
        while self.running:
            try:
                if user32.PeekMessageW(byref(msg), 0, 0, 0, HHC["PM_REMOVE"]):
                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageW(byref(msg))
                else:
                    time.sleep(0.01)
            except Exception:
                # 出现异常直接跳出循环，保证能清理钩子
                break

        # 离开循环之前确保取消钩子
        if self.keyboard_hook:
            try:
                user32.UnhookWindowsHookEx(self.keyboard_hook)
            except Exception:
                pass
            self.keyboard_hook = None
        if self.mouse_hook:
            try:
                user32.UnhookWindowsHookEx(self.mouse_hook)
            except Exception:
                pass
            self.mouse_hook = None
