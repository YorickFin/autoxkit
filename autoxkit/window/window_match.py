

import numpy as np
from PIL import Image
from pathlib import Path
import ctypes
from ctypes import wintypes
from ctypes.wintypes import RECT

from ..tools import RectTuple

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3)
    ]

class WindowMatch:
    """窗口匹配类"""
    def __init__(self, hwnd: int = None):
        self.hwnd = hwnd if hwnd else None

    def _to_gray(self, image: np.ndarray) -> np.ndarray:
        """
        将 RGB 转灰度
        """
        return np.mean(image, axis=2).astype(np.float32)

    def _image_to_numpy(self, image, to_rgb: bool = False) -> np.ndarray:
        """
        将图像转换为 numpy 数组
        Args:
            image: 图像对象
            to_rgb: 是否转换为 RGB 格式
        """
        img_array = np.array(image)
        # 确保是三通道格式
        if img_array.shape[2] != 3:
            img_array = img_array[:, :, :3]

        if to_rgb:
            # BGR -> RGB
            img_array = img_array[:, :, [2, 1, 0]]

        return img_array

    def read_image(self, image_path: str) -> np.ndarray:
        """
        读取图像
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"文件不存在: {image_path}")
        return self._image_to_numpy(Image.open(image_path))

    def save_image(self, image: np.ndarray, image_path: str) -> None:
        """
        保存图像
        """
        image_path = Path(image_path).absolute()
        if not image_path.parent.is_dir():
            raise FileNotFoundError(f"目录不存在: {image_path.parent}")
        Image.fromarray(image).save(image_path)

    def screenshot(self, rect: tuple[int, int, int, int] = None, image_path: str = None) -> np.ndarray:
        """
        截图: 对 self.hwnd 窗口进行区域或完全截图
        Args:
            rect (tuple, None): 矩形区域元组，应包含 (x1, y1, x2, y2)，相对于窗口左上角。
                                   如果为 None，则截取整个窗口。
            image_path (str): 截图保存路径，包含自定义文件名。
        Returns:
            np.ndarray: 截图图像的 numpy 数组表示。
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        try:
            # 获取窗口DC
            hdc = ctypes.windll.user32.GetDC(self.hwnd)

            # 计算窗口客户区大小
            client_rect = RECT()
            ctypes.windll.user32.GetClientRect(self.hwnd, ctypes.byref(client_rect))

            # 确定截图区域
            if rect is None:
                # 截取整个窗口
                x, y, width, height = 0, 0, client_rect.right, client_rect.bottom
            else:
                # 截取指定区域
                rect = RectTuple(*rect)
                x, y, width, height = rect.x1, rect.y1, rect.width, rect.height

            # 创建兼容DC
            hdc_mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc)

            # 创建位图
            hbitmap = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, width, height)

            # 选择位图到兼容DC
            old_bitmap = ctypes.windll.gdi32.SelectObject(hdc_mem, hbitmap)

            # 复制窗口内容到兼容DC
            ctypes.windll.gdi32.BitBlt(
                hdc_mem, 0, 0, width, height,
                hdc, x, y, 0x00CC0020  # SRCCOPY
            )

            # 准备位图信息
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = width
            bmi.bmiHeader.biHeight = -height  # 负值表示从上到下
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 24  # 24位RGB
            bmi.bmiHeader.biCompression = 0  # BI_RGB
            bmi.bmiHeader.biSizeImage = 0
            bmi.bmiHeader.biXPelsPerMeter = 0
            bmi.bmiHeader.biYPelsPerMeter = 0
            bmi.bmiHeader.biClrUsed = 0
            bmi.bmiHeader.biClrImportant = 0

            # 分配内存
            buffer_size = width * height * 3
            buffer = ctypes.create_string_buffer(buffer_size)

            # 获取位图数据
            ctypes.windll.gdi32.GetDIBits(
                hdc_mem, hbitmap, 0, height, buffer, ctypes.byref(bmi), 0
            )

            # 转换为numpy数组
            img_array = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 3)

            # 转为RGB格式数组
            img_array = self._image_to_numpy(img_array, to_rgb=True)
        except Exception as e:
            raise Exception(f"截图失败: {e}")

        finally:
            # 清理资源
            ctypes.windll.gdi32.SelectObject(hdc_mem, old_bitmap)
            ctypes.windll.gdi32.DeleteObject(hbitmap)
            ctypes.windll.gdi32.DeleteDC(hdc_mem)
            ctypes.windll.user32.ReleaseDC(self.hwnd, hdc)

        # 保存截图（如果指定了路径）
        if image_path:
            self.save_image(img_array, image_path)
        return img_array

    def get_pixel_color(self, x: int, y: int, is_return_hex: bool = False) -> str | tuple:
        """
            获取屏幕坐标 (x, y) 处的颜色
        Args:
            x (int): 屏幕坐标 x 轴
            y (int): 屏幕坐标 y 轴
            is_return_hex (bool, optional): 是否返回十六进制字符串。默认 False。
        Returns:
            str | tuple: 十六进制格式字符串，如 #FFAABB 或 (r, g, b) 元组
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        pixel = tuple(int(c) for c in self.screenshot(rect=(x, y, x+1, y+1))[0][0])

        if is_return_hex:   # 返回十六进制字符串
            return f"#{pixel[0]:02X}{pixel[1]:02X}{pixel[2]:02X}"
        return pixel    # 返回 RGB 元组







