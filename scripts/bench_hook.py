# bench_hook.py
"""Hook 端到端延迟基准 + 功能冒烟。

原理：SendInput 合成按键（回调内拦截返回 True，不产生真实输入），
在 SendInput 调用前打点、回调进入时刻再打点，统计端到端延迟分布。

用法：
  python scripts/bench_hook.py                    # 当前生效实现（native 优先）
  python scripts/bench_hook.py --impl fallback    # 强制回退实现（对比基线）
  python scripts/bench_hook.py --n 500            # 事件数
  python scripts/bench_hook.py --mouse            # 额外做鼠标点击冒烟
"""
import argparse
import ctypes
import os
import statistics
import sys
import threading
import time
from ctypes import POINTER, c_int, c_uint, wintypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

user32 = ctypes.WinDLL("user32", use_last_error=True)


# ---------- SendInput 结构定义 ----------
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTU(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTU)]


INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

user32.SendInput.argtypes = [c_uint, POINTER(INPUT), c_int]
user32.SendInput.restype = c_uint


def build_listener(impl):
    import autoxkit.hook.hook_listener as hl

    if impl == "fallback":
        from autoxkit.hook._ctypes_fallback import HookListener
        return HookListener, False
    return hl.HookListener, hl._NATIVE


def bench_keyboard(listener, n):
    """合成 n 次按键，返回 (延迟纳秒列表, 超时丢失数)。回调拦截事件。"""
    results = []
    ev = threading.Event()
    t0 = [0]

    def on_keydown(e):
        t_cb = time.perf_counter_ns()
        results.append(t_cb - t0[0])
        ev.set()
        return True  # 拦截，避免污染真实输入

    listener.add_handler("keydown", on_keydown)
    listener.start()
    time.sleep(0.3)

    missed = 0
    key_down = INPUT()
    key_down.type = INPUT_KEYBOARD
    key_down.u.ki.wVk = 0x41  # 'A'
    key_up = INPUT()
    key_up.type = INPUT_KEYBOARD
    key_up.u.ki.wVk = 0x41
    key_up.u.ki.dwFlags = KEYEVENTF_KEYUP

    for _ in range(n):
        t0[0] = time.perf_counter_ns()
        user32.SendInput(1, ctypes.byref(key_down), ctypes.sizeof(INPUT))
        if not ev.wait(timeout=1.0):
            missed += 1
        ev.clear()
        user32.SendInput(1, ctypes.byref(key_up), ctypes.sizeof(INPUT))
        time.sleep(0.001)

    listener.stop()
    return results, missed


def smoke_mouse(listener):
    """合成一次左键点击，验证鼠标回调与拦截。"""
    got = []
    ev = threading.Event()

    def on_mousedown(e):
        got.append(e)
        ev.set()
        return True  # 拦截

    listener.add_handler("mousedown", on_mousedown)
    listener.start()
    time.sleep(0.2)

    click_down = INPUT()
    click_down.type = INPUT_MOUSE
    click_down.u.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
    click_up = INPUT()
    click_up.type = INPUT_MOUSE
    click_up.u.mi.dwFlags = MOUSEEVENTF_LEFTUP
    user32.SendInput(1, ctypes.byref(click_down), ctypes.sizeof(INPUT))
    ok = ev.wait(timeout=1.0)
    user32.SendInput(1, ctypes.byref(click_up), ctypes.sizeof(INPUT))
    listener.stop()
    listener.remove_handler("mousedown", on_mousedown)

    if ok and got:
        e = got[0]
        print(f"鼠标冒烟 OK: action={e.action} button={e.button} "
              f"position={e.position}")
        return True
    print("鼠标冒烟 失败: 未收到回调")
    return False


def stats(ns_list):
    ms = sorted(x / 1e6 for x in ns_list)
    n = len(ms)
    return {
        "n": n,
        "p50": ms[n // 2],
        "p95": ms[max(int(n * 0.95) - 1, 0)],
        "max": ms[-1],
        "mean": statistics.fmean(ms),
    }


def main():
    ap = argparse.ArgumentParser(description="Hook 延迟基准与冒烟")
    ap.add_argument("--impl", choices=["auto", "native", "fallback"], default="auto")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--mouse", action="store_true", help="额外做鼠标点击冒烟")
    args = ap.parse_args()

    Listener, native = build_listener(args.impl)
    print(f"实现路径: {'native (autoxhook.dll)' if native else 'fallback (纯 ctypes)'}")

    listener = Listener()
    results, missed = bench_keyboard(listener, args.n)
    if results:
        s = stats(results)
        print(
            f"键盘端到端延迟(SendInput→回调): n={s['n']} miss={missed} "
            f"p50={s['p50']:.3f}ms p95={s['p95']:.3f}ms "
            f"max={s['max']:.3f}ms mean={s['mean']:.3f}ms"
        )
    else:
        print(f"键盘基准失败: 0 个事件, miss={missed}")
        sys.exit(1)

    if args.mouse:
        if not smoke_mouse(listener):
            sys.exit(1)

    print("done")


if __name__ == "__main__":
    main()
