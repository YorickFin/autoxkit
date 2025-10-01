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
        """

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

class CLSID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_uint32),
                ("Data2", ctypes.c_uint16),
                ("Data3", ctypes.c_uint16),
                ("Data4", ctypes.c_ubyte * 8)]

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

# 新增的保存图像相关函数
GdipCreateBitmapFromScan0 = gdiplus.GdipCreateBitmapFromScan0
GdipCreateBitmapFromScan0.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
GdipCreateBitmapFromScan0.restype = ctypes.c_int

GdipSaveImageToFile = gdiplus.GdipSaveImageToFile
GdipSaveImageToFile.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(CLSID), ctypes.c_void_p]
GdipSaveImageToFile.restype = ctypes.c_int

# 编码器CLSID
def get_encoder_clsid(format_name):
    """获取指定格式的编码器CLSID"""
    # 定义编码器相关函数
    GdipGetImageEncodersSize = gdiplus.GdipGetImageEncodersSize
    GdipGetImageEncodersSize.argtypes = [ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
    GdipGetImageEncodersSize.restype = ctypes.c_int

    GdipGetImageEncoders = gdiplus.GdipGetImageEncoders
    GdipGetImageEncoders.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
    GdipGetImageEncoders.restype = ctypes.c_int

    class ImageCodecInfo(ctypes.Structure):
        _fields_ = [
            ("Clsid", CLSID),
            ("FormatID", CLSID),
            ("CodecName", ctypes.c_wchar_p),
            ("DllName", ctypes.c_wchar_p),
            ("FormatDescription", ctypes.c_wchar_p),
            ("FilenameExtension", ctypes.c_wchar_p),
            ("MimeType", ctypes.c_wchar_p),
            ("Flags", ctypes.c_uint32),
            ("Version", ctypes.c_uint32),
            ("SigCount", ctypes.c_uint32),
            ("SigSize", ctypes.c_uint32),
            ("SigPattern", ctypes.c_void_p),
            ("SigMask", ctypes.c_void_p)
        ]

    num_encoders = ctypes.c_uint()
    size = ctypes.c_uint()

    # 获取编码器数量和所需缓冲区大小
    if GdipGetImageEncodersSize(ctypes.byref(num_encoders), ctypes.byref(size)) != 0:
        return None

    # 分配缓冲区并获取编码器信息
    encoder_info = (ImageCodecInfo * num_encoders.value)()
    if GdipGetImageEncoders(num_encoders.value, size.value, ctypes.cast(encoder_info, ctypes.c_void_p)) != 0:
        return None

    # 查找指定格式的编码器
    for i in range(num_encoders.value):
        if encoder_info[i].MimeType and encoder_info[i].MimeType.lower() == format_name.lower():
            return encoder_info[i].Clsid

    return None

# 像素格式常量
PixelFormat24bppRGB = 0x21808
PixelFormat32bppARGB = 0x26200A
ImageLockModeRead = 1
ImageLockModeWrite = 2

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
            width, height = int(width.value), int(height.value)

            # 定义锁定区域(整个图像)
            rect = RECT(0, 0, width, height)
            bitmap_data = BitmapData()

            # 锁定位图数据
            status = GdipBitmapLockBits(
                bitmap,
                ctypes.byref(rect),
                ImageLockModeRead,
                PixelFormat32bppARGB,
                ctypes.byref(bitmap_data)
            )
            if status != 0:
                raise RuntimeError(f"Failed to lock bits with status {status}")

            try:
                scan0 = bitmap_data.Scan0
                stride = int(bitmap_data.Stride)
                if not scan0:
                    raise OSError("BitmapData.Scan0 is NULL")
                total_bytes = abs(stride) * height
                buf_type = ctypes.c_ubyte * total_bytes
                buf = buf_type.from_address(
                    ctypes.addressof(
                        ctypes.c_char.from_buffer(
                            ctypes.string_at(
                                scan0, total_bytes
                                ))) if False else scan0)
                addr = ctypes.cast(scan0, ctypes.c_void_p).value
                if addr is None:
                    raise OSError("Failed to obtain scan0 address")
                buf = buf_type.from_address(addr)
                arr = np.frombuffer(buf, dtype=np.uint8)
                arr = arr.reshape(height, abs(stride))

                row_bytes = width * 4
                arr = arr[:, :row_bytes]
                arr = arr.reshape((height, width, 4))
                if bitmap_data.Stride < 0:
                    arr = np.flipud(arr)

                return arr.copy()

            finally:
                # 解锁位图
                GdipBitmapUnlockBits(bitmap, ctypes.byref(bitmap_data))
                if status != 0:
                    raise OSError(f"GdipBitmapUnlockBits failed with status {status}")
        finally:
            # 释放位图
            GdipDisposeImage(bitmap)
    finally:
        # 关闭GDI+
        GdiplusShutdown(token)

def save_image(image: np.ndarray, fname: str=r'examples\temp.png'):
    """
    保存图像到文件

    参数:
        image: numpy数组，形状为(H, W, 3)或(H, W, 4)，数据类型为uint8或float32/float64(会被转换为uint8)
        fname: 保存的文件名，支持常见格式如BMP, JPEG, PNG, GIF等
    """
    if image.dtype != np.uint8:
        # 将浮点图像转换为uint8
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)

    height, width = image.shape[:2]
    channels = image.shape[2] if len(image.shape) == 3 else 1

    # 确定像素格式
    if channels == 3:
        pixel_format = PixelFormat24bppRGB
        stride = width * 3
        # 确保stride是4的倍数
        if stride % 4 != 0:
            stride = (stride // 4 + 1) * 4
    elif channels == 4:
        pixel_format = PixelFormat32bppARGB
        stride = width * 4
    else:
        raise ValueError("只支持3通道(RGB)或4通道(RGBA)图像")

    # 初始化GDI+
    token = ctypes.c_void_p()
    startup_input = GdiplusStartupInput(1, None, False, False)
    status = GdiplusStartup(ctypes.byref(token), ctypes.byref(startup_input), None)
    if status != 0:
        raise RuntimeError(f"GDI+ Startup failed with status {status}")

    try:
        # 创建位图
        bitmap = ctypes.c_void_p()

        # 准备图像数据
        image_data = np.ascontiguousarray(image)

        status = GdipCreateBitmapFromScan0(
            width, height, stride, pixel_format,
            image_data.ctypes.data, ctypes.byref(bitmap)
        )
        if status != 0:
            raise RuntimeError(f"Failed to create bitmap with status {status}")

        try:
            # 根据文件扩展名确定编码器
            ext = fname.lower().split('.')[-1]
            mime_types = {
                'bmp': 'image/bmp',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'tiff': 'image/tiff',
                'tif': 'image/tiff'
            }

            mime_type = mime_types.get(ext, 'image/png')  # 默认为PNG

            # 获取编码器CLSID
            encoder_clsid = get_encoder_clsid(mime_type)
            if encoder_clsid is None:
                raise RuntimeError(f"未找到 {mime_type} 格式的编码器")

            # 保存图像
            status = GdipSaveImageToFile(bitmap, fname, ctypes.byref(encoder_clsid), None)
            if status != 0:
                raise RuntimeError(f"Failed to save image with status {status}")

        finally:
            # 释放位图
            GdipDisposeImage(bitmap)
    finally:
        # 关闭GDI+
        GdiplusShutdown(token)