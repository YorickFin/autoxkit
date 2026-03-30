from autoxkit import ColorMatch
from autoxkit import ImageMatch
from autoxkit import Mouse

def color_match_example():
    color_match = ColorMatch()

    # 坐标颜色匹配
    print(color_match.match(
        source_color=(100, 100),
        target_color=(200, 200),
        similarity=0.8
    ))

    # RGB颜色匹配
    print(color_match.match(
        source_color=(31, 36, 60),
        target_color=(31, 36, 48),
        similarity=0.8
    ))

    # 十六进制颜色匹配
    print(color_match.match(
        source_color='#FF0000',
        target_color='#1F2430',
        similarity=0.8
    ))

    # 混合类型颜色匹配
    print(color_match.match(
        source_color=(100, 100),
        target_color='#1F2430',
        similarity=0.8
    ))

    print(color_match.match(
        source_color=(31, 36, 48),
        target_color='#1F2430',
        similarity=0.8
    ))

    # 获取坐标颜色
    print(color_match.get_pixel_color(x=1906, y=398))     # 默认返回RGB元组
    print(color_match.get_pixel_color(x=1906, y=398, is_return_hex=True))     # 返回十六进制字符串

    # 十六进制颜色转RGB三元组
    print(color_match._hex_to_rgb('#FF0000'))

def image_match_example():
    image_match = ImageMatch()

    # 读取图像，返回numpy数组
    # image = image_match.read_image(r"img\1.png")

    # 保存图像
    # image_match.save_image(image, r"img\2.png")

    # 截图
    # rect = (100, 100, 500, 500)
    # image = image_match.screenshot(rect=rect) # 返回numpy数组
    # image = image_match.screenshot(rect=rect, image_path=r"img\2.png") # 保存截图到路径, 返回numpy数组

    # 图像匹配
    target_image = image_match.read_image(r"img\1.png")
    rect=(0, 0, 100, 100)
    (x, y), sim = image_match.match(target_image=target_image, rect=rect, similarity=0.8)
    if x is not False and y is not False:
        mouse = Mouse()
        mouse.mouse_move(x, y)
    print(x, y, sim)

if __name__ == '__main__':
    # color_match_example()
    # image_match_example()
    pass