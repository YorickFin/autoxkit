import mss
import math

class ColorMatcher:
    def __init__(self):
        self.max_distance = math.sqrt(255**2 * 3)  # RGB 空间最大距离 ≈ 441.67

    def _hex_to_rgb(self, hex_color: str):
        """
        将十六进制颜色字符串转换为 RGB 三元组
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_screen_color(self, x: int, y: int, is_return_hex: bool = True) -> str | tuple:
        """
        获取屏幕坐标 (x, y) 处的颜色，返回十六进制格式字符串，如 #FFAABB
        """
        with mss.mss() as sct:
            # 获取包含该像素的最小区域(1x1像素)
            monitor = {"top": y, "left": x, "width": 1, "height": 1}
            img = sct.grab(monitor)

            # 获取像素颜色(RGB格式)
            pixel = img.pixel(0, 0)

            if is_return_hex:
                # 转换为十六进制字符串
                return f"#{pixel[0]:02X}{pixel[1]:02X}{pixel[2]:02X}"
            else:
                # 返回 RGB 元组
                return pixel

    def color_match(self, source_color: str | tuple, target_color: str | tuple, similarity: float = 0.8) -> tuple:
        """
        匹配两个颜色是否相似
        Parameters:
            (source_color and target_color):
                str: 颜色十六进制字符串， tuple: (r, g, b) | (x, y)

            similarity (float): 相似度阈值，取值范围 0.0 ~ 1.0，越接近 1 越严格。默认值为 0.8。
        Returns:
            tuple: bool(True | False), float(相似度结果值)
        """
        if type(source_color) is str:
            source_color = self._hex_to_rgb(source_color)
        elif type(source_color) is tuple and len(source_color) == 2:
            source_color = self.get_screen_color(*source_color, is_return_hex=False)

        if type(target_color) is str:
            target_color = self._hex_to_rgb(target_color)
        elif type(target_color) is tuple and len(target_color) == 2:
            target_color = self.get_screen_color(*target_color, is_return_hex=False)

        # 计算欧几里得距离
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(source_color, target_color)))
        score = 1 - (distance / self.max_distance)
        return score >= similarity, score