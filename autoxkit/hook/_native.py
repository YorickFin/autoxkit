# _native.py
"""autoxhook.dll 的 ctypes 绑定层。

DLL 为纯 Win32 C 实现（源码见项目 csrc/ 目录），不链接任何 Python
运行时，因此一份 DLL 可跨 Python 3.10~3.13+ 所有版本使用。

Python 侧通过 WINFUNCTYPE 函数指针把回调交给 DLL；DLL 在 C 回调内
完成结构体解析与订阅掩码短路后，仅以纯整数参数调用该指针，
GIL 的获取/释放由 ctypes thunk 自动处理。
"""
import ctypes
import os
from ctypes import POINTER, WINFUNCTYPE, c_char_p, c_int, c_uint

# 回调原型：返回 1 = 拦截事件（吞掉），0 = 放行
# 键盘：(msg, vk, scan, flags, time)
KEY_CB = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_int, c_uint)
# 鼠标：(msg, x, y, data, flags, time)
MOUSE_CB = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_int, c_int, c_uint)

# 事件掩码位（必须与 csrc/autoxhook.h 保持一致）
AXH_KEY_DOWN = 1 << 0
AXH_KEY_UP = 1 << 1
AXH_M_LDOWN = 1 << 0
AXH_M_LUP = 1 << 1
AXH_M_RDOWN = 1 << 2
AXH_M_RUP = 1 << 3
AXH_M_MDOWN = 1 << 4
AXH_M_MUP = 1 << 5
AXH_M_WHEEL = 1 << 6
AXH_M_XDOWN = 1 << 7
AXH_M_XUP = 1 << 8
AXH_M_MOVE = 1 << 9

# axh_start 错误码 → 说明
START_ERRORS = {
    -1: "无空闲监听器槽位",
    -2: "DLL 内部创建线程失败",
    -3: "DLL 钩子初始化超时",
    -4: "键盘钩子安装失败",
    -5: "鼠标钩子安装失败",
    -6: "hook_keyboard 与 hook_mouse 不能同时为 0",
    -7: "DLL 内部创建同步事件失败",
}


def load_dll():
    """加载 _autoxhook.dll 并声明导出函数原型。

    Raises:
        OSError: DLL 缺失、位数不匹配或加载失败（调用方应回退到纯 ctypes 实现）
    """
    dll_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_autoxhook.dll"
    )
    dll = ctypes.WinDLL(dll_path)

    dll.axh_start.argtypes = [c_int, c_int, KEY_CB, MOUSE_CB]
    dll.axh_start.restype = c_int
    dll.axh_stop.argtypes = [c_int]
    dll.axh_stop.restype = c_int
    dll.axh_is_running.argtypes = [c_int]
    dll.axh_is_running.restype = c_int
    dll.axh_set_masks.argtypes = [c_int, c_uint, c_uint]
    dll.axh_set_masks.restype = None
    dll.axh_get_key_state.argtypes = [c_uint]
    dll.axh_get_key_state.restype = c_uint
    dll.axh_get_cursor_pos.argtypes = [POINTER(c_int), POINTER(c_int)]
    dll.axh_get_cursor_pos.restype = c_int
    dll.axh_version.argtypes = []
    dll.axh_version.restype = c_char_p
    return dll


# WM 消息值 → 掩码位（模块加载期构建，热路径零开销）
# 与 constants.Hex_Hook_Code 对应：KeyDown=0x0100 SysKeyDown=0x0104 等
KEY_MSG_BIT = {
    0x0100: AXH_KEY_DOWN,  # WM_KEYDOWN
    0x0104: AXH_KEY_DOWN,  # WM_SYSKEYDOWN
    0x0101: AXH_KEY_UP,    # WM_KEYUP
    0x0105: AXH_KEY_UP,    # WM_SYSKEYUP
}
MOUSE_MSG_BIT = {
    0x0201: AXH_M_LDOWN,   # WM_LBUTTONDOWN
    0x0202: AXH_M_LUP,     # WM_LBUTTONUP
    0x0204: AXH_M_RDOWN,   # WM_RBUTTONDOWN
    0x0205: AXH_M_RUP,     # WM_RBUTTONUP
    0x0207: AXH_M_MDOWN,   # WM_MBUTTONDOWN
    0x0208: AXH_M_MUP,     # WM_MBUTTONUP
    0x020A: AXH_M_WHEEL,   # WM_MOUSEWHEEL
    0x020B: AXH_M_XDOWN,   # WM_XBUTTONDOWN
    0x020C: AXH_M_XUP,     # WM_XBUTTONUP
    0x0200: AXH_M_MOVE,    # WM_MOUSEMOVE（预留）
}
