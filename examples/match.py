from autoxkit.match import Match
from autoxkit.mousekey import Mouse

def match_color_example():
    match = Match()

    # 坐标颜色匹配
    print(match.match_color(
        source_color=(100, 100),
        target_color=(200, 200),
        similarity=0.8
    ))

    # RGB颜色匹配
    print(match.match_color(
        source_color=(31, 36, 60),
        target_color=(31, 36, 48),
        similarity=0.8
    ))

    # 十六进制颜色匹配
    print(match.match_color(
        source_color='#FF0000',
        target_color='#1F2430',
        similarity=0.8
    ))

    # 混合类型颜色匹配
    print(match.match_color(
        source_color=(100, 100),
        target_color='#1F2430',
        similarity=0.8
    ))

    print(match.match_color(
        source_color=(31, 36, 48),
        target_color='#1F2430',
        similarity=0.8
    ))

    # 获取坐标颜色
    print(match.get_pixel_color(x=1700, y=800))     # 默认返回RGB元组
    print(match.get_pixel_color(x=1700, y=800, is_return_hex=True))     # 返回十六进制字符串

def match_image_example():
    match = Match()

    # # 读取图像，返回numpy数组
    # image = match.load_image(r"img\1.png")

    # # 保存图像
    # match.save_image(image, r"img\2.png")

    # # 截图
    # rect = (100, 100, 500, 500)
    # image = match.screenshot(rect=rect) # 返回numpy数组
    # image = match.screenshot(rect=rect, save_path=r"img\2.png") # 保存截图到路径, 返回numpy数组

    # 图像匹配
    target_image = match.load_image(r"img\1.png")
    rect=(0, 0, 100, 100)
    (x, y), sim = match.match_image(target_image=target_image, rect=rect, similarity=0.8)
    if x is not False and y is not False:
        mouse = Mouse()
        mouse.mouse_move(x, y)
    print(x, y, sim)

if __name__ == '__main__':
    # match_color_example()
    match_image_example()