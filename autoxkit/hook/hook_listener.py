# hook_listener.py
"""低级键盘/鼠标钩子监听器。

核心事件链路由 _autoxhook.dll（纯 Win32 C，见项目 csrc/ 目录）承担：
钩子安装、消息泵线程、结构体解析、订阅掩码短路、按键状态跟踪均在 C 层完成，
Python 只接收已解析的语义化整数参数。空订阅事件完全不进入 Python/GIL。

DLL 缺失、位数不匹配或加载失败时，自动回退到 _ctypes_fallback 的纯 ctypes
实现（功能等价，性能为迁移前基线）。
"""
import sys
import threading
from ctypes import POINTER, byref, c_int

from .event import KeyEvent, MouseEvent
from ..constants import Hex_Hook_Code

HHC = Hex_Hook_Code

# ---------- 原生 DLL 加载（失败自动回退） ----------
try:
    from ._native import (
        AXH_KEY_DOWN,
        AXH_KEY_UP,
        AXH_M_LDOWN,
        AXH_M_LUP,
        AXH_M_MDOWN,
        AXH_M_MUP,
        AXH_M_RDOWN,
        AXH_M_RUP,
        AXH_M_WHEEL,
        AXH_M_XDOWN,
        AXH_M_XUP,
        KEY_CB,
        MOUSE_CB,
        START_ERRORS,
        load_dll,
    )
    _dll = load_dll()
    _NATIVE = True
except OSError:
    _dll = None
    _NATIVE = False

if not _NATIVE:
    from ._ctypes_fallback import HookListener
else:

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

            # 注册/启停路径的并发保护（事件热路径无锁）
            self._handlers_lock = threading.Lock()

            # DLL 监听器句柄（<0 表示未启动）
            self._handle = -1
            self._stop_event = threading.Event()

            # 必须保存 WINFUNCTYPE 对象引用，避免被 GC 回收
            self._key_cb = KEY_CB(self._on_key_event)
            self._mouse_cb = MOUSE_CB(self._on_mouse_event)

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

            with self._handlers_lock:
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
                self._refresh_masks()

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

            with self._handlers_lock:
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
                self._refresh_masks()

        # 根据回调列表刷新 DLL 订阅掩码（须持有 _handlers_lock）
        def _refresh_masks(self):
            if self._handle < 0:
                return
            key_mask = 0
            if self._on_keydown:
                key_mask |= AXH_KEY_DOWN
            if self._on_keyup:
                key_mask |= AXH_KEY_UP
            mouse_mask = 0
            if self._on_mousedown:
                mouse_mask |= (
                    AXH_M_LDOWN | AXH_M_RDOWN | AXH_M_MDOWN | AXH_M_XDOWN
                )
            if self._on_mouseup:
                mouse_mask |= AXH_M_LUP | AXH_M_RUP | AXH_M_MUP | AXH_M_XUP
            # 滚轮同时驱动 down/up 两个回调列表，任一非空即订阅
            if self._on_mousedown or self._on_mouseup:
                mouse_mask |= AXH_M_WHEEL
            _dll.axh_set_masks(self._handle, key_mask, mouse_mask)

        # 获取当前鼠标位置
        def get_mouse_position(self):
            """
                获取当前鼠标位置
            Returns:
                tuple[int, int]: 鼠标位置 (x, y)
            """
            x = c_int(0)
            y = c_int(0)
            if _dll.axh_get_cursor_pos(byref(x), byref(y)) == 0:
                return (x.value, y.value)
            import ctypes

            raise ctypes.WinError(ctypes.get_last_error())

        # 内部键盘回调（由 DLL 的 C 回调以纯整数参数调用，仅订阅事件会到达）
        def _on_key_event(self, msg, vk_code, scan_code, flags, time):
            if msg in (HHC["KeyDown"], HHC["SysKeyDown"]):
                event = KeyEvent('KeyDown', vk_code)
                for cb in self._on_keydown:
                    try:
                        result = cb(event)
                        if result is True:
                            return 1  # 截断事件传播
                    except ValueError as e:
                        print(f"[hook_listener] ValueError in keydown callback: {e}", file=sys.stderr)
                    except Exception as e:
                        print(f"[hook_listener] Exception in keydown callback: {e}", file=sys.stderr)
            else:
                event = KeyEvent('KeyUp', vk_code)
                for cb in self._on_keyup:
                    try:
                        result = cb(event)
                        if result is True:
                            return 1  # 截断事件传播
                    except ValueError as e:
                        print(f"[hook_listener] ValueError in keyup callback: {e}", file=sys.stderr)
                    except Exception as e:
                        print(f"[hook_listener] Exception in keyup callback: {e}", file=sys.stderr)
            return 0  # 放行

        # 内部鼠标回调（由 DLL 的 C 回调以纯整数参数调用）
        # data 语义由 msg 决定：滚轮=有符号原始 delta；X键=1(MSide1)/2(MSide2)；其余=0
        def _on_mouse_event(self, msg, x, y, data, flags, time):
            if msg == HHC["MWheel"]:
                delta = data / 120
                if delta > 0:
                    blocked = False
                    event = MouseEvent("MouseDown", "MUWheel", x, y, distance=delta)
                    for cb in self._on_mousedown:
                        try:
                            result = cb(event)
                            if result is True:
                                blocked = True
                        except Exception as e:
                            print(f"[hook_listener] Exception in mousedown callback: {e}", file=sys.stderr)

                    event = MouseEvent("MouseUp", "MUWheel", x, y, distance=delta)
                    for cb in self._on_mouseup:
                        try:
                            result = cb(event)
                            if result is True:
                                blocked = True
                        except Exception as e:
                            print(f"[hook_listener] Exception in mouseup callback: {e}", file=sys.stderr)

                    if blocked:
                        return 1    # 截断事件传播

                elif delta < 0:
                    blocked = False
                    event = MouseEvent("MouseDown", "MDWheel", x, y, distance=delta)
                    for cb in self._on_mousedown:
                        try:
                            result = cb(event)
                            if result is True:
                                blocked = True
                        except Exception as e:
                            print(f"[hook_listener] Exception in mousedown callback: {e}", file=sys.stderr)

                    event = MouseEvent("MouseUp", "MDWheel", x, y, distance=delta)
                    for cb in self._on_mouseup:
                        try:
                            result = cb(event)
                            if result is True:
                                blocked = True
                        except Exception as e:
                            print(f"[hook_listener] Exception in mouseup callback: {e}", file=sys.stderr)

                    if blocked:
                        return 1    # 截断事件传播

            elif msg in (HHC["MLeftDown"], HHC["MRightDown"], HHC["MiddleDown"], HHC["XDown"]):
                button = self._get_mouse_button(msg, data)
                event = MouseEvent("MouseDown", button, x, y)
                for cb in self._on_mousedown:
                    try:
                        result = cb(event)
                        if result is True:
                            return 1  # 截断事件传播
                    except Exception as e:
                        print(f"[hook_listener] Exception in mousedown callback: {e}", file=sys.stderr)

            elif msg in (HHC["MLeftUp"], HHC["MRightUp"], HHC["MiddleUp"], HHC["XUp"]):
                button = self._get_mouse_button(msg, data)
                event = MouseEvent("MouseUp", button, x, y)
                for cb in self._on_mouseup:
                    try:
                        result = cb(event)
                        if result is True:
                            return 1  # 截断事件传播
                    except Exception as e:
                        print(f"[hook_listener] Exception in mouseup callback: {e}", file=sys.stderr)

            return 0  # 放行

        # 辅助函数：获取鼠标按键名称（C 侧已解析 X 键编号到 data）
        @staticmethod
        def _get_mouse_button(wParam, data):
            if wParam in (HHC["MLeftDown"], HHC["MLeftUp"]):
                return 'MLeft'
            elif wParam in (HHC["MRightDown"], HHC["MRightUp"]):
                return 'MRight'
            elif wParam in (HHC["MiddleDown"], HHC["MiddleUp"]):
                return 'Middle'
            elif wParam in (HHC["XDown"], HHC["XUp"]):
                return 'MSide1' if data == HHC["MSide1"] else 'MSide2'

        # 启动监听（DLL 内部创建消息泵线程并安装钩子）
        def start(self):
            with self._handlers_lock:
                if self._handle >= 0:
                    return
                ret = _dll.axh_start(1, 1, self._key_cb, self._mouse_cb)
                if ret < 0:
                    raise RuntimeError(
                        "autoxhook 启动失败: "
                        + START_ERRORS.get(ret, f"错误码 {ret}")
                    )
                self._handle = ret
                self._stop_event.clear()
                self._refresh_masks()

        # 停止监听并取消钩子（DLL 内部时序：先断 Python 触达，再卸钩，再释放槽位）
        def stop(self):
            with self._handlers_lock:
                if self._handle < 0:
                    self._stop_event.set()
                    return
                _dll.axh_stop(self._handle)
                self._handle = -1
            self._stop_event.set()

        # 阻塞等待直到停止
        def wait(self):
            self._stop_event.wait()

        def __del__(self):
            try:
                self.stop()
            except Exception:
                pass
