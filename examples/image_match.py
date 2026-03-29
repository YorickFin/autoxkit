import time
from autoxkit import ImageMatcher
from autoxkit import Mouse

image_matcher = ImageMatcher()

# # 读取图像，返回numpy数组
# image = image_matcher.read_image(r"img\1.png")
# # 保存图像
# image_matcher.save_image(image, r"img\2.png")

# # 截图
# rect = (100, 100, 500, 500)
# image = image_matcher.screenshot(rect=rect) # 返回numpy数组
# image = image_matcher.screenshot(rect=rect, image_path=r"img\2.png") # 保存截图到路径, 返回numpy数组


# 图像匹配
# target_image = image_matcher.read_image(r"img\1.png")
# source_image = image_matcher.screenshot(rect=(0, 0, 600, 600))
# start_time = time.time()
# (x, y), sim = image_matcher.image_match(source_image, target_image, similarity=0.9)
# print(f"用时：{time.time() - start_time}")
# print(x, y, sim)

# if x:
#     mouse = Mouse()
#     mouse.mouse_move(x, y)


