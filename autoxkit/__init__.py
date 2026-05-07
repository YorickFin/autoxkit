import importlib
import sys
from types import ModuleType

__all__ = [
    # 鼠标控制
    "Mouse",

    # 键盘控制
    "KeyBoard",

    # 鼠标键盘钩子
    "HookListener", "KeyEvent", "MouseEvent",

    # 热键监听器
    "HotkeyListener",

    # 颜色匹配
    "MatchColor",

    # 图像匹配
    "MatchImage",

    # 窗口控制
    "Window",

    # 码表
    "Hex_Key_Code", "Hex_Mouse_Code", "Hex_Hook_Code",
]


class _LazyModule(ModuleType):
    """延迟导入模块，实现按需加载"""

    _MODULE_MAPPING = {
        # mousekey 模块
        "Mouse": (".mousekey", "Mouse"),
        "KeyBoard": (".mousekey", "KeyBoard"),
        "HookListener": (".mousekey", "HookListener"),
        "KeyEvent": (".mousekey", "KeyEvent"),
        "MouseEvent": (".mousekey", "MouseEvent"),
        "HotkeyListener": (".mousekey", "HotkeyListener"),
        # icmatch 模块
        "MatchColor": (".icmatch", "MatchColor"),
        "MatchImage": (".icmatch", "MatchImage"),
        # window 模块
        "Window": (".window", "Window"),
        # constants 模块
        "Hex_Key_Code": (".constants", "Hex_Key_Code"),
        "Hex_Mouse_Code": (".constants", "Hex_Mouse_Code"),
        "Hex_Hook_Code": (".constants", "Hex_Hook_Code"),
    }

    def __getattr__(self, name: str):
        if name in self._MODULE_MAPPING:
            module_path, attr_name = self._MODULE_MAPPING[name]
            module = importlib.import_module(module_path, package=__name__)
            return getattr(module, attr_name)
        return super().__getattribute__(name)


# 用延迟导入类替换当前模块
_lazy_module = _LazyModule(__name__)
_lazy_module.__dict__.update(sys.modules[__name__].__dict__)
sys.modules[__name__] = _lazy_module