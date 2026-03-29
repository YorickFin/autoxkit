

class WindowMatch:
    """窗口匹配类"""
    def __init__(self, hwnd: int = None):
        self.hwnd = hwnd if hwnd else None

