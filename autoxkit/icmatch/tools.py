import ctypes
import numpy as np

class RectTuple(tuple):
    """
    矩形元组类，确保参数满足以下要求：
    1. 包含4个int类型元素
    2. 第三个元素必须大于第一个元素（x2 > x1）
    3. 第四个元素必须大于第二个元素（y2 > y1）
    """
    def __new__(cls, x1: int, y1: int, x2: int, y2: int):
        """
        创建新的RectTuple实例

        参数:
            x1: 左上角x坐标
            y1: 左上角y坐标
            x2: 右下角x坐标
            y2: 右下角y坐标

        异常:
            TypeError: 当参数不是int类型时抛出
            ValueError: 当不满足大小关系时抛出
        """
        # 检查类型
        if not isinstance(x1, int):
            raise TypeError(f"x1必须是int类型，而不是 {type(x1).__name__}")
        if not isinstance(y1, int):
            raise TypeError(f"y1必须是int类型，而不是 {type(y1).__name__}")
        if not isinstance(x2, int):
            raise TypeError(f"x2必须是int类型，而不是 {type(x2).__name__}")
        if not isinstance(y2, int):
            raise TypeError(f"y2必须是int类型，而不是 {type(y2).__name__}")

        # 检查大小关系
        if x2 <= x1:
            raise ValueError(f"x2必须大于x1，当前 x1={x1}, x2={x2}")

        if y2 <= y1:
            raise ValueError(f"y2必须大于y1，当前 y1={y1}, y2={y2}")

        # 创建tuple实例
        return super().__new__(cls, (x1, y1, x2, y2))

    @property
    def x1(self):
        """返回左上角x1坐标"""
        return self[0]

    @property
    def y1(self):
        """返回左上角y1坐标"""
        return self[1]

    @property
    def x2(self):
        """返回右下角x2坐标"""
        return self[2]

    @property
    def y2(self):
        """返回右下角y2坐标"""
        return self[3]

    def __repr__(self):
        """返回对象的字符串表示"""
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"


# 定义GDI+结构体和常量
class GdiplusStartupInput(ctypes.Structure):
    _fields_ = [
        ("GdiplusVersion", ctypes.c_uint32),
        ("DebugEventCallback", ctypes.c_void_p),
        ("SuppressBackgroundThread", ctypes.c_bool),
        ("SuppressExternalCodecs", ctypes.c_bool),
    ]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

class BitmapData(ctypes.Structure):
    _fields_ = [
        ("Width", ctypes.c_uint),
        ("Height", ctypes.c_uint),
        ("Stride", ctypes.c_int),
        ("PixelFormat", ctypes.c_int),
        ("Scan0", ctypes.c_void_p),
        ("Reserved", ctypes.c_uint),
    ]

# 加载GDI+库
gdiplus = ctypes.WinDLL("gdiplus.dll")

# 定义函数原型
GdiplusStartup = gdiplus.GdiplusStartup
GdiplusStartup.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(GdiplusStartupInput), ctypes.c_void_p]
GdiplusStartup.restype = ctypes.c_int

GdipCreateBitmapFromFile = gdiplus.GdipCreateBitmapFromFile
GdipCreateBitmapFromFile.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p)]
GdipCreateBitmapFromFile.restype = ctypes.c_int

GdipGetImageWidth = gdiplus.GdipGetImageWidth
GdipGetImageWidth.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
GdipGetImageWidth.restype = ctypes.c_int

GdipGetImageHeight = gdiplus.GdipGetImageHeight
GdipGetImageHeight.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
GdipGetImageHeight.restype = ctypes.c_int

GdipBitmapLockBits = gdiplus.GdipBitmapLockBits
GdipBitmapLockBits.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT), ctypes.c_int, ctypes.c_int, ctypes.POINTER(BitmapData)]
GdipBitmapLockBits.restype = ctypes.c_int

GdipBitmapUnlockBits = gdiplus.GdipBitmapUnlockBits
GdipBitmapUnlockBits.argtypes = [ctypes.c_void_p, ctypes.POINTER(BitmapData)]
GdipBitmapUnlockBits.restype = ctypes.c_int

GdipDisposeImage = gdiplus.GdipDisposeImage
GdipDisposeImage.argtypes = [ctypes.c_void_p]
GdipDisposeImage.restype = ctypes.c_int

GdiplusShutdown = gdiplus.GdiplusShutdown
GdiplusShutdown.argtypes = [ctypes.c_void_p]
GdiplusShutdown.restype = None

# 像素格式常量
PixelFormat24bppRGB = 0x21808
ImageLockModeRead = 1

def read_image(fpath: str) -> np.ndarray:
    # 初始化GDI+
    token = ctypes.c_void_p()
    startup_input = GdiplusStartupInput(1, None, False, False)
    status = GdiplusStartup(ctypes.byref(token), ctypes.byref(startup_input), None)
    if status != 0:
        raise RuntimeError(f"GDI+ Startup failed with status {status}")

    try:
        # 加载图像
        bitmap = ctypes.c_void_p()
        status = GdipCreateBitmapFromFile(fpath, ctypes.byref(bitmap))
        if status != 0:
            raise RuntimeError(f"Failed to load image with status {status}")

        try:
            # 获取图像尺寸
            width = ctypes.c_uint()
            height = ctypes.c_uint()
            GdipGetImageWidth(bitmap, ctypes.byref(width))
            GdipGetImageHeight(bitmap, ctypes.byref(height))
            width, height = width.value, height.value

            # 定义锁定区域(整个图像)
            rect = RECT(0, 0, width, height)
            bitmap_data = BitmapData()

            # 锁定位图数据
            status = GdipBitmapLockBits(
                bitmap,
                ctypes.byref(rect),
                ImageLockModeRead,
                PixelFormat24bppRGB,
                ctypes.byref(bitmap_data)
            )
            if status != 0:
                raise RuntimeError(f"Failed to lock bits with status {status}")

            try:
                # 获取像素数据
                stride = bitmap_data.Stride
                pixel_data = ctypes.cast(bitmap_data.Scan0, ctypes.POINTER(ctypes.c_ubyte))
                # 创建numpy数组
                img_array = np.ctypeslib.as_array(pixel_data, shape=(height, stride))
                # 转换为标准RGB格式(高度, 宽度, 3)
                img_array = img_array[:, :width * 3].reshape(height, width, 3)
                # 复制数据以避免内存问题
                img_array = np.copy(img_array)
            finally:
                # 解锁位图
                GdipBitmapUnlockBits(bitmap, ctypes.byref(bitmap_data))
        finally:
            # 释放位图
            GdipDisposeImage(bitmap)
    finally:
        # 关闭GDI+
        GdiplusShutdown(token)

    return np.array(img_array, dtype=np.float32)