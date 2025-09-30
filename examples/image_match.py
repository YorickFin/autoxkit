import time
from autoxkit import ImageMatcher

image_matcher = ImageMatcher()

# # 读取图像，返回numpy数组
# image = image_matcher.read_image("image.png")
# print(image)
# print(image.shape)
# print(image.dtype)

# # 截图
# rect = (100, 100, 500, 500)
# image = image_matcher.get_screen_image(rect=rect) # 返回numpy数组
# image = image_matcher.get_screen_image(rect=rect, fpath=r"examples") # 保存截图到路径, 返回numpy数组
# print(image)
# image = image_matcher.get_screen_image(rect=rect, is_return_image_data=True) # 返回图像数据
# print(image)

# # 图像数据转换为numpy数组
# image_data = image_matcher.get_screen_image(rect=rect, is_return_image_data=True) # 返回图像数据
# image = image_matcher.image_to_numpy(image_data)

# 图像匹配
rect = (100, 100, 200, 200)
target_image = image_matcher.get_screen_image(rect=rect, fpath=r"examples")
# target_image = image_matcher.read_image(r"examples\screen_image.png")
rect = (0, 0, 300, 300)
source_image = image_matcher.get_screen_image(rect=rect)
start_time = time.time()
result = image_matcher.image_match(source_image, target_image)
print(f"用时：{time.time() - start_time}")
print(result)

