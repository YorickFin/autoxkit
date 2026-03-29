import importlib
import sys
from types import ModuleType

__all__ = [
    # 窗口控制
    'Window'
]


class _LazyModule(ModuleType):
    """延迟导入模块，实现按需加载"""

    _MODULE_MAPPING = {
        "Window": (".window", "Window"),
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
