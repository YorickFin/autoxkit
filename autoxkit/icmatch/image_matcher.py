import os
import mss
import numpy as np
from scipy import signal
from mss.tools import to_png
from mss.screenshot import ScreenShot

from .tools import read_image, RectTuple


class ImageMatcher:
    def __init__(self):
        self.sct = mss.mss()

    def image_to_numpy(self, image) -> np.ndarray:
        """
        将图像转换为 numpy 数组
        """
        img_array = np.array(image, dtype=np.float32)
        if img_array.shape[2] != 3:
            img_array = img_array[:, :, :3]
        return img_array

    def read_image(self, fpath: str) -> np.ndarray:
        """
        读取图像文件并转换为 numpy 数组
        """
        return read_image(fpath)

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

        return self._match_ncc(source_image, target_image, similarity)

    def _match_ncc(self, source_image: np.ndarray, target_image: np.ndarray,
                   similarity: float = 0.8
                   ) -> tuple[tuple, float]:
        """
        使用归一化互相关(NCC)方法匹配图像
        """
        nccs = []
        for c in range(source_image.shape[2]):
            s_channel = source_image[..., c]
            t_channel = target_image[..., c]

            # 计算分母部分，避免除零
            t_norm = np.linalg.norm(t_channel)
            if t_norm == 0:
                # 如果模板全为零，跳过该通道或处理特殊情况
                continue

            # 计算分子：互相关
            numerator = signal.correlate2d(s_channel, t_channel, mode='valid')
            # 计算分母：局部能量 × 模板能量
            s_squared = signal.correlate2d(s_channel**2, np.ones_like(t_channel), mode='valid')
            denominator = np.sqrt(s_squared) * t_norm

            # 避免除零，将分母为零的位置设为很小的正数
            denominator[denominator == 0] = 1e-8

            ncc = numerator / denominator
            nccs.append(ncc)

        if not nccs:  # 所有通道都跳过了
            return None

        ncc_mean = np.mean(nccs, axis=0)

        # 找到最佳匹配位置
        max_sim = np.max(ncc_mean)
        if max_sim >= similarity:
            y, x = np.unravel_index(np.argmax(ncc_mean), ncc_mean.shape)
            return (x, y), max_sim
        else:
            return False, max_sim

