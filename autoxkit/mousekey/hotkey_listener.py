# hotkey_listener.py
import time
import threading
from .hook_listener import KeyEvent, Hex_Key_Code


class HotkeyListener:
    """
        快捷键监听器
    Args:
        timeout (float): 组合键按下的最大时间窗口，默认2秒
    """

    def __init__(self, hook_listener, timeout=2.0):
        self.timeout = timeout
        self.hotkeys = {}  # name -> {"keys": [...], "func": func}
        self.current_keys = []  # 当前按下的顺序
        self.start_time = None
        self.lock = threading.Lock()

        self.hook_listener = hook_listener
        self.hook_listener.add_handler("keydown", self._on_hot_key_down)
        self.hook_listener.add_handler("keyup", self._on_hot_key_up)

    def _key_in_hex_codes(self, key: str):
        """判断按键是否存在于Hex_Key_Code中"""
        if key in Hex_Key_Code:
            return True
        raise ValueError(f"key not found in Hex_Key_Code: {key}")

    def add_hotkey(self, name: str, keys: list, func):
        """
            注册快捷键
        Args:
            name (str): 快捷键名称
            keys (list): 快捷键组合，例如 ["Ctrl", "A"]
            func (callable): 触发函数
        Returns:
            str: 注册成功信息
        """
        vk_codes = [Hex_Key_Code[k] for k in keys if self._key_in_hex_codes(k)]
        with self.lock:
            self.hotkeys[name] = {"keys": vk_codes, "func": func}
        return f"successful registration of hotkey: {name}, keys: {keys}, func: {func}"

    def update_hotkey(self, name: str, keys: list = None, func=None):
        """
            根据名称修改快捷键或触发函数
        Args:
            name (str): 快捷键名称
            keys (list): 新的快捷键组合，例如 ["Ctrl", "A"]
            func (callable): 新的触发函数
        Returns:
            str: 修改成功信息
        """
        with self.lock:
            if name not in self.hotkeys:
                raise ValueError(f"name not found in hotkeys: {name}")
            if keys:
                self.hotkeys[name]["keys"] = [Hex_Key_Code[k] for k in keys if self._key_in_hex_codes(k)]
            if func:
                self.hotkeys[name]["func"] = func
            return f"successful update of hotkey: {name}, keys: {self.hotkeys[name]['keys']}, func: {self.hotkeys[name]['func']}"

    def remove_hotkey(self, name: str):
        """
            根据名称注销快捷键
        Args:
            name (str): 快捷键名称
        Returns:
            str: 注销成功信息
        """
        with self.lock:
            if name in self.hotkeys:
                del self.hotkeys[name]
                return f"successful unregistration of hotkey: {name}, keys: {self.hotkeys[name]['keys']}, func: {self.hotkeys[name]['func']}"
            raise ValueError(f"name not found in hotkeys: {name}")

    def _on_hot_key_down(self, event: KeyEvent):
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
                    self.start_time = now
                    return True
        return False

    def _on_hot_key_up(self, event: KeyEvent):
        vk_code = event.key_code
        # 只移除释放的键
        if vk_code in self.current_keys:
            self.current_keys.remove(vk_code)
        # 如果所有键都释放了，重置时间
        if not self.current_keys:
            self.start_time = None
        return False

    def start(self):
        self.hook_listener.start()

    def stop(self):
        self.hook_listener.stop()

    def wait(self):
        self.hook_listener.wait()

    def __del__(self):
        self.stop()
