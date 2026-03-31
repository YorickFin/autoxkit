from autoxkit import MatchColor
from autoxkit import MatchImage
from autoxkit import Mouse

def match_color_example():
    match_color = MatchColor()

    # 坐标颜色匹配
    print(match_color.match(
        source_color=(100, 100),
        target_color=(200, 200),
        similarity=0.8
    ))

    # RGB颜色匹配
    print(match_color.match(
        source_color=(31, 36, 60),
        target_color=(31, 36, 48),
        similarity=0.8
    ))

    # 十六进制颜色匹配
    print(match_color.match(
        source_color='#FF0000',
        target_color='#1F2430',
        similarity=0.8
    ))

    # 混合类型颜色匹配
    print(match_color.match(
        source_color=(100, 100),
        target_color='#1F2430',
        similarity=0.8
    ))

    print(match_color.match(
        source_color=(31, 36, 48),
        target_color='#1F2430',
        similarity=0.8
    ))

    # 获取坐标颜色
    print(match_color.get_pixel_color(x=1700, y=800))     # 默认返回RGB元组
    print(match_color.get_pixel_color(x=1700, y=800, is_return_hex=True))     # 返回十六进制字符串

    # 十六进制颜色转RGB三元组
    print(match_color._hex_to_rgb('#FF0000'))

def match_image_example():
    match_image = MatchImage()

    # 读取图像，返回numpy数组
    # image = match_image.read_image(r"img\1.png")

    # 保存图像
    # match_image.save_image(image, r"img\2.png")

    # 截图
    # rect = (100, 100, 500, 500)
    # image = match_image.screenshot(rect=rect) # 返回numpy数组
    # image = match_image.screenshot(rect=rect, save_path=r"img\2.png") # 保存截图到路径, 返回numpy数组

    # 图像匹配
    target_image = match_image.read_image(r"img\1.png")
    rect=(0, 0, 100, 100)
    (x, y), sim = match_image.match(target_image=target_image, rect=rect, similarity=0.8)
    if x is not False and y is not False:
        mouse = Mouse()
        mouse.mouse_move(x, y)
    print(x, y, sim)

    # 图像预处理
    # image = match_image.read_image(r"examples\text.jpg")
    # image = match_image.proc_image(image, colors=["#070506"], threshold=200)
    # match_image.save_image(image, r"examples\text_proc.png")

if __name__ == '__main__':
    # match_color_example()
    match_image_example()
    pass