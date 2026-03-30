
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

    def screenshot(self, rect: tuple[int, int, int, int] = None, save_path: str = None) -> np.ndarray:
        """
        截图:
            对 self.hwnd 窗口进行区域或完全截图
        Args:
            rect (tuple, None): 矩形区域元组，应包含 (x1, y1, x2, y2)，相对于窗口左上角。
                                   如果为 None，则截取整个窗口。
            save_path (str, None): 截图保存路径，包含自定义文件名。
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
        if save_path:
            self.save_image(img_array, save_path)
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

    def match_color(self, source_color: str | tuple, target_color: str | tuple, similarity: float = 0.8) -> tuple:
        """
            匹配颜色
        Args:
            (source_color and target_color):
                str: 颜色十六进制字符串， tuple: (r, g, b) | (x, y)

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

    def proc_image(self, image: np.ndarray, colors: list[tuple[int, int, int]] | list[str],
                   threshold: int = 150, is_magnify: bool = False) -> np.ndarray:
        """
        简介:
            预处理图像, 方便给 tesseract 等库做文字识别,
            将指定颜色转换为黑色, 其他为白色, 然后做超分辨率放大。
        Args:
            image (np.ndarray): 待预处理图像
            colors (list[tuple[int, int, int]] | list[str]): 支持 RGB 元组和十六进制字符串。
            threshold (int, optional): 颜色距离阈值, 用于颜色毛边判定。默认值为 150。
            is_magnify (bool, optional): 是否做超分辨率放大。默认值为 False。
        Returns:
            np.ndarray: 预处理后的图像
        """

        def color_filter(image, target_colors) -> np.ndarray:
            """
            颜色过滤器
            """
            target_colors = np.array(target_colors).reshape(-1, 1, 1, 3)     # 转换为 numpy 数组
            dists = np.linalg.norm(image - target_colors, axis=3)        # 计算颜色距离
            mask = np.any(dists < threshold, axis=0)                    # 生成掩码
            image = np.full_like(image, 255)                            # 创建白底图像
            image[mask] = 0                                            # 黑色像素
            return image

        image = np.array(image, dtype=np.uint8)

        # 如果是十六进制字符串, 转换为 RGB 元组
        target_colors = []
        for color in colors:
            if isinstance(color, str):
                target_colors.append(tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)))
            else:
                target_colors.append(color)

        image = color_filter(image, target_colors)
        # 超分辨率放大: 双三次插值
        if is_magnify:
            image = ndimage.zoom(image, (3, 3, 1), order=3)
        image = color_filter(image, (0, 0, 0))
        return image




