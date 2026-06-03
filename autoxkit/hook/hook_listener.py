# hook_listener.py
import ctypes
from ctypes import wintypes, Structure, POINTER, CFUNCTYPE, byref
import threading
import time
from .event import KeyEvent, MouseEvent
from ..constants import Hex_Hook_Code

HHC = Hex_Hook_Code

# 消息泵空闲轮询间隔（秒），无消息时休眠此时间以释放 CPU
MSG_POLL_INTERVAL = 0.001

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

# ---------- 回调类型 ----------
HOOKPROC = CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# ---------- 加载 DLL 并声明 API 签名 ----------
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
    每个实例可以独立运行、独立添加多个回调（keydown/keyup/mousedown/mouseup）
    """
    def __init__(self):
        # 回调列表（支持多个回调）
        self._on_keydown = []
        self._on_keyup = []
        self._on_mousedown = []
        self._on_mouseup = []

        # 钩子与线程状态
        self._thread = None
        self.keyboard_hook = None
        self.mouse_hook = None
        self._stop_event = threading.Event()

        # 必须保存CFUNCTYPE对象引用，避免被GC回收
        # 绑定到实例的 method（bound method）是合法的 callable
        self._keyboard_proc_c = HOOKPROC(self._keyboard_proc)
        self._mouse_proc_c = HOOKPROC(self._mouse_proc)

        # module handles
        self._hMod = kernel32.GetModuleHandleW(None)

    # 注册回调
    def add_handler(self, event_type: str, func):
        """
            注册回调
        Args:
            event_type (str): 事件类型，可选值为 "keydown"、"keyup"、"mousedown"、"mouseup"
            func (callable): 回调函数，参数为 KeyEvent 或 MouseEvent 对象
        """
        if not callable(func):
            raise ValueError("func must be a callable object")

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
        """
            移除回调
        Args:
            event_type (str): 事件类型，可选值为 "keydown"、"keyup"、"mousedown"、"mouseup"
            func (callable): 回调函数，参数为 KeyEvent 或 MouseEvent 对象
        """
        if not callable(func):
            raise ValueError("func must be a callable object")

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
        """
            获取当前鼠标位置
        Returns:
            tuple[int, int]: 鼠标位置 (x, y)
        """
        pt = wintypes.POINT()
        if user32.GetCursorPos(byref(pt)):
            return (pt.x, pt.y)
        else:
            raise ctypes.WinError(ctypes.get_last_error())

    # 内部键盘回调（bound method -> can be wrapped by CFUNCTYPE）
    def _keyboard_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            try:
                kbd = ctypes.cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
                if wParam in (HHC["KeyDown"], HHC["SysKeyDown"]):
                    event = KeyEvent('KeyDown', kbd.vkCode)
                    for cb in self._on_keydown:
                        try:
                            result = cb(event)
                            if result is True:
                                return 1  # 截断事件传播
                        except ValueError as e:
                            print(f"[hook_listener] ValueError in keydown callback: {e}", file=__import__('sys').stderr)
                        except Exception as e:
                            print(f"[hook_listener] Exception in keydown callback: {e}", file=__import__('sys').stderr)
                elif wParam in (HHC["KeyUp"], HHC["SysKeyUp"]):
                    event = KeyEvent('KeyUp', kbd.vkCode)
                    for cb in self._on_keyup:
                        try:
                            result = cb(event)
                            if result is True:
                                return 1  # 截断事件传播
                        except ValueError as e:
                            print(f"[hook_listener] ValueError in keyup callback: {e}", file=__import__('sys').stderr)
                        except Exception as e:
                            print(f"[hook_listener] Exception in keyup callback: {e}", file=__import__('sys').stderr)
            except Exception as e:
                print(f"[hook_listener] Exception in _keyboard_proc: {e}", file=__import__('sys').stderr)

        return user32.CallNextHookEx(self.keyboard_hook, nCode, wParam, lParam)

    # 内部鼠标回调
    def _mouse_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            try:
                ms = ctypes.cast(lParam, POINTER(MSLLHOOKSTRUCT)).contents
                x, y = ms.pt.x, ms.pt.y

                if wParam in (HHC["MLeftDown"], HHC["MRightDown"], HHC["MiddleDown"], HHC["XDown"]):
                    button = self._get_mouse_button(wParam, ms.mouseData)
                    event = MouseEvent("MouseDown", button, x, y)
                    for cb in self._on_mousedown:
                        try:
                            result = cb(event)
                            if result is True:
                                return 1  # 截断事件传播
                        except Exception as e:
                            print(f"[hook_listener] Exception in mousedown callback: {e}", file=__import__('sys').stderr)

                elif wParam in (HHC["MLeftUp"], HHC["MRightUp"], HHC["MiddleUp"], HHC["XUp"]):
                    button = self._get_mouse_button(wParam, ms.mouseData)
                    event = MouseEvent("MouseUp", button, x, y)
                    for cb in self._on_mouseup:
                        try:
                            result = cb(event)
                            if result is True:
                                return 1  # 截断事件传播
                        except Exception as e:
                            print(f"[hook_listener] Exception in mouseup callback: {e}", file=__import__('sys').stderr)
            except Exception as e:
                print(f"[hook_listener] Exception in _mouse_proc: {e}", file=__import__('sys').stderr)

        return user32.CallNextHookEx(self.mouse_hook, nCode, wParam, lParam)

    # 辅助函数：获取鼠标按键名称
    def _get_mouse_button(self, wParam, mouseData):
        if wParam in (HHC["MLeftDown"], HHC["MLeftUp"]):
            return 'MLeft'
        elif wParam in (HHC["MRightDown"], HHC["MRightUp"]):
            return 'MRight'
        elif wParam in (HHC["MiddleDown"], HHC["MiddleUp"]):
            return 'Middle'
        elif wParam in (HHC["XDown"], HHC["XUp"]):
            high = (mouseData >> 16) & 0xFFFF
            return 'MSide1' if high == HHC["MSide1"] else 'MSide2'

    # 启动监听（新线程 pump message loop）
    def start(self):
        # 如果线程已在运行，直接返回
        if self._thread and self._thread.is_alive():
            return
        # 如果停止事件已设置，先清除以便重新开始
        if self._stop_event.is_set():
            self._stop_event.clear()
        self._thread = threading.Thread(target=self._thread_func, daemon=True)
        self._thread.start()

    # 停止监听并取消钩子
    def stop(self):
        self._stop_event.set()
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

    # 阻塞等待直到停止
    def wait(self):
        self._stop_event.wait()

    # 线程体：注册钩子并 pump 消息
    def _thread_func(self):
        try:
            # 注册钩子（低级钩子一般可以传 module handle + threadId=0）
            self.keyboard_hook = user32.SetWindowsHookExW(HHC["Key_LL"], self._keyboard_proc_c, self._hMod, 0)
            self.mouse_hook = user32.SetWindowsHookExW(HHC["Mouse_LL"], self._mouse_proc_c, self._hMod, 0)
        except Exception:
            # 若注册失败，设置停止事件并结束
            self._stop_event.set()
            return

        msg = wintypes.MSG()
        while not self._stop_event.is_set():
            try:
                # 使用 PeekMessageW 配合超时，以便可以检查 _stop_event
                if user32.PeekMessageW(byref(msg), 0, 0, 0, 1):  # PM_REMOVE = 1
                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageW(byref(msg))
                else:
                    # 无消息时休眠，避免 CPU 忙等
                    time.sleep(MSG_POLL_INTERVAL)
            except Exception:
                # 记录异常但不退出循环，确保钩子持续工作
                print("[hook_listener] Exception in message pump", file=__import__('sys').stderr)
                continue

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

    def __del__(self):
        self.stop()
