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
    "ColorMatcher",

    # 图像匹配
    "ImageMatcher",
]


class _LazyModule(ModuleType):
    """延迟导入模块，实现按需加载"""

    _MODULE_MAPPING = {
        # mousekey 模块
        "Mouse": ("autoxkit.mousekey", "Mouse"),
        "KeyBoard": ("autoxkit.mousekey", "KeyBoard"),
        "HookListener": ("autoxkit.mousekey", "HookListener"),
        "KeyEvent": ("autoxkit.mousekey", "KeyEvent"),
        "MouseEvent": ("autoxkit.mousekey", "MouseEvent"),
        "HotkeyListener": ("autoxkit.mousekey", "HotkeyListener"),
        # icmatch 模块
        "ColorMatcher": ("autoxkit.icmatch", "ColorMatcher"),
        "ImageMatcher": ("autoxkit.icmatch", "ImageMatcher"),
    }

    def __getattr__(self, name: str):
        if name in self._MODULE_MAPPING:
            module_path, attr_name = self._MODULE_MAPPING[name]
            module = importlib.import_module(module_path)
            return getattr(module, attr_name)
        return super().__getattribute__(name)


# 用延迟导入类替换当前模块
_lazy_module = _LazyModule(__name__)
_lazy_module.__dict__.update(sys.modules[__name__].__dict__)
sys.modules[__name__] = _lazy_module