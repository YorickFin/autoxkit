# hotkey_listener.py
import time
import threading
from .hook_listener import HookListener, Hex_Key_Code


class HotkeyListener:
    def __init__(self, timeout=2.0):
        """
        :param timeout: 组合键按下的最大时间窗口，默认2秒
        """
        self.timeout = timeout
        self.hotkeys = {}  # name -> {"keys": [...], "func": func}
        self.current_keys = []  # 当前按下的顺序
        self.start_time = None
        self.lock = threading.Lock()

        self.hook_listener = HookListener()
        self.hook_listener.add_handler("keydown", self._on_keydown)
        self.hook_listener.add_handler("keyup", self._on_keyup)
        self.hook_listener.start()

    def register_hotkey(self, name, keys, func):
        """注册快捷键"""
        vk_codes = [Hex_Key_Code[k] for k in keys]
        with self.lock:
            self.hotkeys[name] = {"keys": vk_codes, "func": func}

    def update_hotkey(self, name, keys=None, func=None):
        """根据名称修改快捷键或触发函数"""
        with self.lock:
            if name not in self.hotkeys:
                return False
            if keys:
                self.hotkeys[name]["keys"] = [Hex_Key_Code[k] for k in keys]
            if func:
                self.hotkeys[name]["func"] = func
            return True

    def unregister_hotkey(self, name):
        """根据名称删除快捷键"""
        with self.lock:
            if name in self.hotkeys:
                del self.hotkeys[name]
                return True
            return False

    def _on_keydown(self, event):
        vk_code = event.key_code
        now = time.time()

        if not self.start_time:
            self.start_time = now
            self.current_keys = [vk_code]
        else:
            if now - self.start_time > self.timeout:
                # 超时重置
                self.start_time = now
                self.current_keys = [vk_code]
            else:
                self.current_keys.append(vk_code)

        # 检查匹配
        with self.lock:
            for hotkey in self.hotkeys.values():
                if self.current_keys == hotkey["keys"]:
                    hotkey["func"]()
                    self.current_keys = []
                    self.start_time = None

    def _on_keyup(self, event):
        # 只要有按键释放，就重置序列
        self.current_keys = []
        self.start_time = None

    def stop(self):
        self.hook_listener.stop()