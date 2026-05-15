import numpy as np
from pathlib import Path
from PIL import Image

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
        Args:
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

    @property
    def width(self):
        """返回矩形宽度"""
        return self.x2 - self.x1

    @property
    def height(self):
        """返回矩形高度"""
        return self.y2 - self.y1

    def __repr__(self):
        """返回对象的字符串表示"""
        return f"({self.x1}, {self.y1}, {self.x2}, {self.y2})"


class DataHeader:
    """
    数据头类，用于存储图像数据的元信息
    """
    def __init__(self):
        self._load_images = dict()

    def hex_to_rgb(self, hex_color: str):
        """
        将十六进制颜色字符串转换为 RGB 三元组
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_gray(self, image: np.ndarray) -> np.ndarray:
        """
        将 RGB 转灰度
        """
        return np.mean(image, axis=2).astype(np.float32)

    def image_to_numpy(self, image, to_rgb: bool = False) -> np.ndarray:
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

    def cache_image(self, image_path: str, image: np.ndarray) -> None:
        """
            缓存图像
        Args:
            image_path (str): 图像文件路径
        """
        self._load_images[image_path] = image

    def clear_cache_images(self) -> None:
        """
            清空缓存图像
        """
        self._load_images.clear()

    def load_image(self, image_path: str) -> np.ndarray:
        """
            加载图像
        Args:
            image_path (str): 图像文件路径
        Returns:
            np.ndarray: 图像的 numpy 数组表示
        """
        if image_path in self._load_images:
            return self._load_images[image_path]
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"文件不存在: {image_path}")
        image_np = self._image_to_numpy(Image.open(image_path))
        self.cache_image(str(image_path), image_np)
        return image_np

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


