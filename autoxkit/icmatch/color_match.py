import mss
import math

def get_screen_color(x: int, y: int) -> str:
    """
    获取屏幕坐标 (x, y) 处的颜色，返回十六进制格式字符串，如 #FFAABB
    """
    with mss.mss() as sct:
        # 获取包含该像素的最小区域(1x1像素)
        monitor = {"top": y, "left": x, "width": 1, "height": 1}
        img = sct.grab(monitor)

        # 获取像素颜色(RGB格式)
        pixel = img.pixel(0, 0)

        # 转换为十六进制字符串
        return f"#{pixel[0]:02X}{pixel[1]:02X}{pixel[2]:02X}"


def hex_to_rgb(hex_color: str):
    """
    将十六进制颜色字符串转换为 RGB 三元组
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def color_match(color1: str, color2: str, similarity: float) -> bool:
    """
    判断两个颜色是否足够相似，基于 RGB 欧几里得距离。
    similarity: 相似度阈值，取值范围 0.0 ~ 1.0，越接近 1 越严格。
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    # 计算欧几里得距离
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))
    max_distance = math.sqrt(255**2 * 3)  # RGB 空间最大距离 ≈ 441.67

    similarity_score = 1 - (distance / max_distance)
    return similarity_score >= similarity