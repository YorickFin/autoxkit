import importlib
import sys
from types import ModuleType

__all__ = [
    # 鼠标控制
    'Mouse',

    # 键盘控制
    "KeyBoard",

    # 鼠标键盘钩子
    "HookListener", "KeyEvent", "MouseEvent",

    # 热键监听器
    "HotkeyListener",
]


class _LazyModule(ModuleType):
    """延迟导入模块，实现按需加载"""

    _MODULE_MAPPING = {
        "Mouse": (".mouse", "Mouse"),
        "KeyBoard": (".keyboard", "KeyBoard"),
        "HookListener": (".hook_listener", "HookListener"),
        "KeyEvent": (".hook_listener", "KeyEvent"),
        "MouseEvent": (".hook_listener", "MouseEvent"),
        "HotkeyListener": (".hotkey_listener", "HotkeyListener"),
    }

    def __getattr__(self, name: str):
        if name in self._MODULE_MAPPING:
            module_path, attr_name = self._MODULE_MAPPING[name]
            module = importlib.import_module(module_path, package=__name__)
            return getattr(module, attr_name)
        return super().__getattribute__(name)


_lazy_module = _LazyModule(__name__)
_lazy_module.__dict__.update(sys.modules[__name__].__dict__)
sys.modules[__name__] = _lazy_module
