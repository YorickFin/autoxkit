from autoxkit import HookListener, HotkeyListener

def save_func():
    print("保存 - Ctrl+S 触发")

def find_func():
    print("查找 - Ctrl+F 触发")

def save_as_func():
    print("另存 - Ctrl+Shift+S 触发")

def delete_func():
    print("删除 - Shift+Delete 触发")

hook_listener = HookListener()
hotkey_listener = HotkeyListener(hook_listener=hook_listener, timeout=2.0)
hotkey_listener.add_hotkey("保存", ("Lctrl", "S"), lambda: save_func())
hotkey_listener.add_hotkey("查找", ("Lctrl", "F"), lambda: find_func())
hotkey_listener.add_hotkey("另存", ("Lctrl", "Lshift", "S"), lambda: save_as_func())
hotkey_listener.add_hotkey("删除", ("Lshift", "Delete"), lambda: delete_func())
hotkey_listener.start()

if __name__ == "__main__":
    try:
        hotkey_listener.wait()
    except Exception:
        hotkey_listener.stop()
