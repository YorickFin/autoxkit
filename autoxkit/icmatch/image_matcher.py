import os
import mss
import numpy as np
from scipy import ndimage
from scipy.signal import fftconvolve
from mss.tools import to_png
from mss.screenshot import ScreenShot

from .tools import RectTuple


class ImageMatcher:
    def __init__(self):
        self.sct = mss.mss()

    def _to_gray(self, image: np.ndarray) -> np.ndarray:
        """
        将 RGB 转灰度
        """
        return np.mean(image, axis=2).astype(np.float32)

    def image_to_numpy(self, image) -> np.ndarray:
        """
        将图像转换为 numpy 数组
        """
        img_array = np.array(image)
        if img_array.shape[2] != 3:
            img_array = img_array[:, :, :3]
        return img_array

    def get_screen_image(
        self, rect: tuple[int, int, int, int],
        fpath: str=None, is_return_image_data: bool = False
        ) -> np.ndarray | ScreenShot:
        """
            获取显示器 rect 区域的图像
        Parameters:
            rect (tuple): 矩形区域元组，应包含 (x1, y1, x2, y2)。
            fpath (str, optional): 截图保存路径，不包含文件名，默认文件名为 screen_image.png。
        Returns:
            np.ndarray | ScreenShot: 截图对象或 numpy 数组，根据 is_return_image_data 确定返回类型。
            如果 fpath 不为 None，则保存截图到目录。
        """
        rect = RectTuple(*rect)

        screen_image = self.sct.grab(rect)

        # 验证路径
        if fpath is not None:
            if not os.path.exists(fpath):
                raise ValueError(f"路径 {fpath} 不存在")
            if not os.path.isdir(fpath):
                raise ValueError(f"路径 {fpath} 不是目录")
            to_png(screen_image.rgb, screen_image.size, output=os.path.join(fpath, "screen_image.png"))
            print("截图已保存： " + os.path.join(fpath, "screen_image.png"))

        if is_return_image_data:
            return screen_image
        else:
            return self.image_to_numpy(screen_image)

    def image_match(self, source_image: np.ndarray, target_image: np.ndarray,
                    similarity: float = 0.8
                    ) -> tuple[tuple, float]:
        """
        匹配图像
        Parameters:
            source_image (np.ndarray): 待匹配图像
            target_image (np.ndarray): 目标图像
            similarity (float, optional): 相似度阈值，默认 0.8。
        Returns:
            tuple[tuple, float]: 匹配结果元组，包含匹配位置和相似度。
        """
        source_image = np.array(source_image, dtype=np.float32)
        target_image = np.array(target_image, dtype=np.float32)

        return self._match_ncc(source_image, target_image, similarity)

    def _match_ncc(self, source_image: np.ndarray, target_image: np.ndarray,
                   similarity: float = 0.8
                   ) -> tuple[tuple, float]:
        """
        简介:
            使用 FFT 加速的归一化互相关(NCC)方法匹配图像 (灰度)。

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
            y, x = np.unravel_index(np.argmax(ncc), ncc.shape)
            return (int(x), int(y)), round(float(max_sim), 3)
        else:
            return False, round(float(max_sim), 3)

    def preprocess_image(self, image: np.ndarray,
                         colors: list[tuple[int, int, int]] | list[str],
                         threshold: int = 150, scale_factor: int = 3
                         ) -> np.ndarray:
        """
        简介:
            预处理图像, 方便给 tesseract 等库做文字识别,
            将指定颜色转换为黑色, 其他为白色, 然后做超分辨率放大。
        Parameters:
            image (np.ndarray): 待预处理图像
            colors (list[tuple[int, int, int]] | list[str]): 支持 RGB 元组和十六进制字符串。
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
        image = ndimage.zoom(image, (scale_factor, scale_factor, 1), order=3)
        image = color_filter(image, (0, 0, 0))
        return image