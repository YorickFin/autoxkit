from autoxkit import ColorMatcher

color_matcher = ColorMatcher()

# 坐标颜色匹配
print(color_matcher.color_match(
    source_color=(100, 100),
    target_color=(200, 200),
    similarity=0.8
))

# RGB颜色匹配
print(color_matcher.color_match(
    source_color=(31, 36, 60),
    target_color=(31, 36, 48),
    similarity=0.8
))

# 十六进制颜色匹配
print(color_matcher.color_match(
    source_color='#FF0000',
    target_color='#1F2430',
    similarity=0.8
))

# 混合类型颜色匹配
print(color_matcher.color_match(
    source_color=(100, 100),
    target_color='#1F2430',
    similarity=0.8
))

print(color_matcher.color_match(
    source_color=(31, 36, 48),
    target_color='#1F2430',
    similarity=0.8
))

# 获取坐标颜色
print(color_matcher.get_screen_color(x=100, y=100))     # 默认返回十六进制字符串
print(color_matcher.get_screen_color(x=100, y=100, is_return_hex=False))     # 返回RGB元组

# 十六进制颜色转RGB三元组
print(color_matcher._hex_to_rgb('#FF0000'))