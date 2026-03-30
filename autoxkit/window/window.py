
import ctypes
from ctypes import wintypes
from ctypes.wintypes import RECT
from .window_action import WindowAction
from .window_match import WindowMatch

user32 = ctypes.windll.user32

# 定义回调函数类型
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class Window(WindowAction, WindowMatch):

    def __init__(self, title_name: str='', class_name: str='', hwnd: int = None):
        self.title_name = title_name if title_name else None
        self.class_name = class_name if class_name else None
        self.hwnd = hwnd
        if hwnd or title_name or class_name:
            if self.bind_window():
                WindowAction.__init__(self, self.hwnd)
                WindowMatch.__init__(self, self.hwnd)

    def activate_window(self):
        """激活窗口"""
        if self.hwnd:
            user32.SetForegroundWindow(self.hwnd)
            user32.SetFocus(self.hwnd)

    @property
    def size(self) -> tuple:
        """返回窗口大小"""
        if self.hwnd:
            rect = RECT()
            user32.GetClientRect(self.hwnd, ctypes.byref(rect))
            return (rect.right - rect.left, rect.bottom - rect.top)
        raise ValueError("窗口句柄未设置")

    def bind_window(self):
        """
        通过 title_name、class_name 或 hwnd 查找窗口。
        支持查找子窗口（二级、三级等），无需指定父窗口。
        优先级: hwnd > title_name > class_name
        找到窗口后补全所有属性
        """
        if self.hwnd is not None:
            # 验证句柄是否有效
            if user32.IsWindow(self.hwnd):
                self._fill_window_info(self.hwnd)
                return self.hwnd
            else:
                raise ValueError(f"无效的窗口句柄: {self.hwnd}")

        # 递归查找所有窗口
        if self.title_name or self.class_name:
            hwnd = self._find_window()
            if hwnd:
                self.hwnd = hwnd
                self._fill_window_info(hwnd)
                return hwnd

        raise RuntimeError(
            f"未找到窗口: title_name={self.title_name}, class_name={self.class_name}"
        )

    def _find_window(self) -> int:
        """
        递归查找所有窗口（包括顶级窗口和所有子窗口），无需指定父窗口
        """
        found_hwnd = 0

        def enum_window_callback(hwnd, lparam):
            nonlocal found_hwnd
            if found_hwnd != 0:
                return True

            # 检查当前窗口
            if self._match_window(hwnd):
                found_hwnd = hwnd
                return False

            # 递归查找子窗口
            def enum_child_callback(child_hwnd, child_lparam):
                nonlocal found_hwnd
                if found_hwnd != 0:
                    return True

                if self._match_window(child_hwnd):
                    found_hwnd = child_hwnd
                    return False

                # 继续递归更深级别的子窗口
                user32.EnumChildWindows(child_hwnd, EnumWindowsProc(enum_child_callback), 0)
                return True

            user32.EnumChildWindows(hwnd, EnumWindowsProc(enum_child_callback), 0)
            return True

        user32.EnumWindows(EnumWindowsProc(enum_window_callback), 0)
        return found_hwnd

    def _match_window(self, hwnd: int) -> bool:
        """检查窗口是否匹配条件"""
        title_name = self._get_window_title(hwnd)
        class_name = self._get_window_class(hwnd)

        match_title = self.title_name and self.title_name == title_name
        match_class = self.class_name and self.class_name == class_name

        if self.class_name and self.title_name:
            return match_class and match_title
        elif self.title_name:
            return match_title
        elif self.class_name:
            return match_class
        return False

    def _get_window_title(self, hwnd: int) -> str:
        """获取窗口标题"""
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            return buffer.value
        return ""

    def _get_window_class(self, hwnd: int) -> str:
        """获取窗口类名"""
        buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buffer, 256)
        return buffer.value

    def _fill_window_info(self, hwnd: int):
        """补全窗口信息"""
        if self.title_name is None:
            self.title_name = self._get_window_title(hwnd)
        if self.class_name is None:
            self.class_name = self._get_window_class(hwnd)

    def __str__(self) -> str:
        return f"Window(title_name={self.title_name}, class_name={self.class_name}, hwnd={self.hwnd})"


