import time
from autoxkit.mousekey import HotkeyListener

def save_func():
    print("保存 - Ctrl+S 触发")

def find_func():
    print("查找 - Ctrl+F 触发")

def save_as_func():
    print("另存 - Ctrl+Shift+S 触发")

def delete_func():
    print("删除 - Shift+S 触发")

hotkeylistener = HotkeyListener(timeout=2.0)
hotkeylistener.register_hotkey("保存", ("Lctrl", "S"), save_func)
hotkeylistener.register_hotkey("查找", ("Lctrl", "F"), find_func)
hotkeylistener.register_hotkey("另存", ("Lctrl", "Lshift", "S"), save_as_func)
hotkeylistener.register_hotkey("删除", ("Lshift", "Delete"), delete_func)

if __name__ == "__main__":
    print("Hotkey Listener 正在运行... 按 Ctrl+C 退出")

    try:
        while True:
            time.sleep(1)
    except Exception:
        hotkeylistener.stop()
        print("已退出")