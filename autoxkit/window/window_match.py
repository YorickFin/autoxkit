import mss
import math
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
from scipy.signal import fftconvolve
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
        self.sct = mss.mss()

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

    def _hex_to_rgb(self, hex_color: str):
        """
        将十六进制颜色字符串转换为 RGB 三元组
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def read_image(self, image_path: str) -> np.ndarray:
        """
            读取图像
        Args:
            image_path (str): 图像文件路径
        Returns:
            np.ndarray: 图像的 numpy 数组表示
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"文件不存在: {image_path}")
        return self._image_to_numpy(Image.open(image_path))

    def save_image(self, image: np.ndarray, image_path: str) -> None:
        """
            保存图像
        Args:
            image (np.ndarray): 图像的 numpy 数组表示
            image_path (str): 图像保存路径
        """
        image_path = Path(image_path).absolute()
        if not image_path.parent.is_dir():
            raise FileNotFoundError(f"目录不存在: {image_path.parent}")
        Image.fromarray(image).save(image_path)

    def screenshot(self, rect: tuple[int, int, int, int]=None, save_path: str = None) -> np.ndarray:
        """
            截图
        Args:
            rect (tuple, None): 矩形区域元组，应包含 (x1, y1, x2, y2)，相对于窗口左上角。
                                   如果为 None，则截取整个窗口。
            save_path (str, None): 截图保存路径，包含自定义文件名。
        Returns:
            np.ndarray: 截图图像的 numpy 数组表示。
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        # 尝试多种截图方法
        methods = [
            self._screenshot_mss,
            self._screenshot_printwindow,
            self._screenshot_bitblt
        ]

        last_error = None
        for method in methods:
            # print(f"尝试方法: {method.__name__}")
            try:
                img_array = method(rect)
                # 检查是否为纯黑图像
                if not self._is_black_image(img_array):
                    # 保存截图（如果指定了路径）
                    if save_path:
                        self.save_image(img_array, save_path)
                    return img_array
                last_error = f"{method.__name__} 截图结果为纯黑"
            except Exception as e:
                last_error = f"{method.__name__} 失败: {e}"

        raise Exception(f"所有截图方法都失败: {last_error}")

    def _is_black_image(self, img_array: np.ndarray, threshold: int = 10, ratio: float = 0.95) -> bool:
        """
            检查图像是否为纯黑或接近纯黑
        Args:
            img_array (np.ndarray): 图像数组
            threshold (int): 像素值阈值，低于此值视为黑色像素
            ratio (float): 黑色像素比例阈值，超过此比例认为是纯黑图像
        Returns:
            bool: 如果黑色像素比例超过阈值，返回True
        """
        black_mask = np.all(img_array < threshold, axis=2)
        black_ratio = np.sum(black_mask) / black_mask.size
        return black_ratio > ratio

    def _screenshot_bitblt(self, rect: tuple[int, int, int, int] = None) -> np.ndarray:
        """
        使用 BitBlt 方法截图
        """
        hdc = None
        hdc_mem = None
        hbitmap = None
        old_bitmap = None

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
            return img_array
        finally:
            # 清理资源
            if old_bitmap and hdc_mem:
                ctypes.windll.gdi32.SelectObject(hdc_mem, old_bitmap)
            if hbitmap:
                ctypes.windll.gdi32.DeleteObject(hbitmap)
            if hdc_mem:
                ctypes.windll.gdi32.DeleteDC(hdc_mem)
            if hdc:
                ctypes.windll.user32.ReleaseDC(self.hwnd, hdc)

    def _screenshot_printwindow(self, rect: tuple[int, int, int, int] = None) -> np.ndarray:
        """
        使用 PrintWindow 方法截图
        注意：PrintWindow API 无法直接指定区域，因此先截取整个窗口，
              然后通过数组切片提取指定区域。
        """
        hdc = None
        hdc_mem = None
        hbitmap = None
        old_bitmap = None

        try:
            # 获取窗口DC
            hdc = ctypes.windll.user32.GetDC(self.hwnd)

            # 获取整个窗口的矩形（包括标题栏、边框）
            window_rect = RECT()
            ctypes.windll.user32.GetWindowRect(self.hwnd, ctypes.byref(window_rect))
            window_width = window_rect.right - window_rect.left
            window_height = window_rect.bottom - window_rect.top

            # 获取客户区的矩形
            client_rect = RECT()
            ctypes.windll.user32.GetClientRect(self.hwnd, ctypes.byref(client_rect))

            # 获取客户区左上角在屏幕上的坐标
            client_point = wintypes.POINT(0, 0)
            ctypes.windll.user32.ClientToScreen(self.hwnd, ctypes.byref(client_point))

            # 计算客户区相对于窗口左上角的偏移
            client_offset_x = client_point.x - window_rect.left
            client_offset_y = client_point.y - window_rect.top

            # 确定截图区域
            if rect is None:
                # 截取整个客户区窗口
                x, y, width, height = client_offset_x, client_offset_y, client_rect.right, client_rect.bottom
            else:
                # 截取指定区域（相对于客户区）
                rect = RectTuple(*rect)
                # 转换为相对于整个窗口的坐标
                x, y, width, height = rect.x1 + client_offset_x, rect.y1 + client_offset_y, rect.width, rect.height

            # 创建兼容DC
            hdc_mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc)

            # 创建位图（使用整个窗口大小）
            hbitmap = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, window_width, window_height)

            # 选择位图到兼容DC
            old_bitmap = ctypes.windll.gdi32.SelectObject(hdc_mem, hbitmap)

            # 使用 PrintWindow 方法截图
            result = ctypes.windll.user32.PrintWindow(self.hwnd, hdc_mem, 0x00000002)
            if not result:
                raise Exception("PrintWindow 调用失败")

            # 准备位图信息
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = window_width
            bmi.bmiHeader.biHeight = -window_height  # 负值表示从上到下
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 24  # 24位RGB
            bmi.bmiHeader.biCompression = 0  # BI_RGB
            bmi.bmiHeader.biSizeImage = 0
            bmi.bmiHeader.biXPelsPerMeter = 0
            bmi.bmiHeader.biYPelsPerMeter = 0
            bmi.bmiHeader.biClrUsed = 0
            bmi.bmiHeader.biClrImportant = 0

            # 分配内存
            buffer_size = window_width * window_height * 3
            buffer = ctypes.create_string_buffer(buffer_size)

            # 获取位图数据
            ctypes.windll.gdi32.GetDIBits(
                hdc_mem, hbitmap, 0, window_height, buffer, ctypes.byref(bmi), 0
            )

            # 转换为numpy数组
            img_array = np.frombuffer(buffer, dtype=np.uint8).reshape(window_height, window_width, 3)

            # 转为RGB格式数组
            img_array = self._image_to_numpy(img_array, to_rgb=True)

            # 确保裁剪区域在窗口范围内
            # 计算裁剪区域的边界
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(window_width, x + width)
            y2 = min(window_height, y + height)

            # 确保裁剪区域有效
            if x1 < x2 and y1 < y2:
                img_array = img_array[y1:y2, x1:x2]
            else:
                # 如果裁剪区域无效，返回空图像
                img_array = np.zeros((0, 0, 3), dtype=np.uint8)

            return img_array
        finally:
            # 清理资源
            if old_bitmap and hdc_mem:
                ctypes.windll.gdi32.SelectObject(hdc_mem, old_bitmap)
            if hbitmap:
                ctypes.windll.gdi32.DeleteObject(hbitmap)
            if hdc_mem:
                ctypes.windll.gdi32.DeleteDC(hdc_mem)
            if hdc:
                ctypes.windll.user32.ReleaseDC(self.hwnd, hdc)

    def _screenshot_mss(self, rect: tuple[int, int, int, int] = None) -> np.ndarray:
        """
            截图
        Args:
            rect (RectTuple, optional): 截图区域。默认 None。
        Returns:
            np.ndarray: 截图图像
        """
        # 窗口客户区位置
        client_point = wintypes.POINT(0, 0)
        ctypes.windll.user32.ClientToScreen(self.hwnd, ctypes.byref(client_point))

        # 窗口客户区大小
        _rect = RECT()
        ctypes.windll.user32.GetClientRect(self.hwnd, ctypes.byref(_rect))
        window_width = _rect.right - _rect.left
        window_height = _rect.bottom - _rect.top

        if rect is None:
            # 截取整个客户区窗口
            rect = (
                client_point.x,
                client_point.y,
                client_point.x + window_width,
                client_point.y + window_height
            )
            rect = RectTuple(*rect)
        else:
            # 截取指定区域（相对于客户区）
            rect = (
                rect[0] + client_point.x,
                rect[1] + client_point.y,
                rect[2] + client_point.x,
                rect[3] + client_point.y
            )
            rect = RectTuple(*rect)

        screen_image = self.sct.grab(rect)
        screen_image = self._image_to_numpy(screen_image, to_rgb=True)
        return screen_image

    def get_pixel_color(self, x: int, y: int, is_return_hex: bool = False) -> str | tuple:
        """
            获取窗口坐标 (x, y) 处的颜色
        Args:
            x (int): 窗口坐标 x 轴
            y (int): 窗口坐标 y 轴
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

    def match_color(self, source_color: str | tuple, target_color: str | tuple, similarity: float = 0.8) -> tuple:
        """
            匹配颜色
        Args:
            source_color (str | tuple): 源颜色 (str: 颜色十六进制字符串， tuple: (r, g, b) | (x, y))
            target_color (str | tuple): 目标颜色 (str: 颜色十六进制字符串， tuple: (r, g, b) | (x, y))
            similarity (float): 相似度阈值，取值范围 0.0 ~ 1.0，越接近 1 越严格。默认值为 0.8。
        Returns:
            tuple: bool(True | False), float(相似度结果值)
        """
        if type(source_color) is str:
            source_color = self._hex_to_rgb(source_color)
        elif type(source_color) is tuple and len(source_color) == 2:
            source_color = self.get_pixel_color(*source_color, is_return_hex=False)

        if type(target_color) is str:
            target_color = self._hex_to_rgb(target_color)
        elif type(target_color) is tuple and len(target_color) == 2:
            target_color = self.get_pixel_color(*target_color, is_return_hex=False)

        # 计算欧几里得距离
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(source_color, target_color)))
        score = 1 - (distance / self.max_distance)
        return score >= similarity, round(score, 3)

    def match_image(self, target_image: np.ndarray=None, rect: tuple[int, int, int, int]=None,
                    similarity: float=0.8):
        """
            匹配图像
        Args:
            target_image (np.ndarray): 目标图像
            rect (tuple): 矩形区域元组，应包含 (x1, y1, x2, y2)，不提供时默认匹配整个窗口。
            similarity (float): 相似度阈值，默认 0.8。
        Returns:
            tuple[tuple[int, int], float]: 匹配结果元组，包含匹配位置和相似度。
        """
        if not self.hwnd:
            raise ValueError("窗口句柄未设置")

        # 检查参数
        if target_image is None:
            raise ValueError("必须提供 target_image 参数")

        # 截取屏幕区域
        rect = RectTuple(*rect) if rect is not None else RectTuple(0, 0, self.size[0], self.size[1])
        source_image = self.screenshot(rect)

        # 转换为 float32 精度
        source_image = np.array(source_image, dtype=np.float32)
        target_image = np.array(target_image, dtype=np.float32)

        # 调用匹配方法
        (x, y), sim = self._match_ncc(source_image, target_image, similarity)

        # 调整坐标以对应窗口坐标
        if x is not False and y is not False:
            x, y = x + rect.x1, y + rect.y1
            return (int(x), int(y)), sim
        else:
            return (False, False), sim

    def _match_ncc(self, source_image: np.ndarray, target_image: np.ndarray,
                   similarity: float = 0.8) -> tuple[tuple, float]:
        """
        简介:
            使用 FFT 加速的归一化互相关(NCC)方法匹配图像 (灰度)，并使用边缘检测进行二次验证。

        性能参考:
            性能为 0.006秒 ~ 0.2秒 ~ 0.6秒 之间，取决于图像大小。
            0.006秒 = source_image: 300x300, target_image: 100x100
            0.2  秒 = source_image: 2560x1440, target_image: 100x100
            0.6  秒 = source_image: 2560x1440, target_image: 2460x1340
        """

        # 转灰度
        s_channel = self._to_gray(source_image)
        t_channel = self._to_gray(target_image)

        # 模板能量
        t_norm = np.linalg.norm(t_channel)
        if t_norm == 0:
            return False, 0.0

        # 计算分子：互相关 (FFT 卷积)
        numerator = fftconvolve(s_channel, np.flipud(np.fliplr(t_channel)), mode='valid')

        # 计算分母：局部能量 × 模板能量
        s_squared = fftconvolve(s_channel**2, np.ones_like(t_channel), mode='valid')
        denominator = np.sqrt(s_squared) * t_norm

        denominator[denominator == 0] = 1e-8  # 避免除零

        ncc = numerator / denominator

        # 找到最佳匹配位置
        max_sim = np.max(ncc)
        if max_sim >= similarity:
            # 左上角坐标
            y, x = np.unravel_index(np.argmax(ncc), ncc.shape)
            h, w = target_image.shape[:2]

            # 确保提取区域在源图像范围内
            if y + h <= source_image.shape[0] and x + w <= source_image.shape[1]:
                # 提取匹配区域
                matched_region = source_image[y:y+h, x:x+w]

                # 边缘检测二次验证
                target_edges = self._edge_detection(target_image)
                matched_edges = self._edge_detection(matched_region)

                # 计算边缘相似度
                edge_numerator = np.sum(target_edges * matched_edges)
                edge_denominator = np.sqrt(np.sum(target_edges**2) * np.sum(matched_edges**2))
                edge_denominator = max(edge_denominator, 1e-8)  # 避免除零
                edge_sim = edge_numerator / edge_denominator

                # 只有当边缘相似度也达到阈值时，才认为匹配成功
                if edge_sim >= similarity:
                    # 中心坐标
                    center_x = x + w // 2
                    center_y = y + h // 2
                    return (int(center_x), int(center_y)), round(float(max_sim), 3)

        return (False, False), round(float(max_sim), 3)

    def _edge_detection(self, image: np.ndarray) -> np.ndarray:
        """
        使用 Sobel 算子进行边缘检测
        """
        # 转灰度
        if len(image.shape) == 3:
            gray = self._to_gray(image)
        else:
            gray = image

        # Sobel 边缘检测
        sobel_x = ndimage.sobel(gray, axis=0, mode='constant')
        sobel_y = ndimage.sobel(gray, axis=1, mode='constant')
        edges = np.sqrt(sobel_x**2 + sobel_y**2)

        # 归一化
        edges = edges / (np.max(edges) + 1e-8)
        return edges
