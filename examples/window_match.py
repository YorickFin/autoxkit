import time
from autoxkit.window import Window

def window_match():
    # 绑定窗口，指定窗口标题和类名（可单选一）
    window = Window(title_name='MuMuNxDevice', class_name='Qt5156QWindowIcon')
    # 前台被覆盖窗口可以正常操作，不需要激活，最小化到任务栏的窗口需要先激活
    window.activate_window()
    time.sleep(1)

    # 截图
    # image = window.screenshot()       #全窗口截图
    # image = window.screenshot(rect=None, save_path=r"img\3.png")    #全窗口截图, 保存到路径
    # image = window.screenshot(rect=(100, 100, 200, 200), save_path=r"img\3.png")    #区域截图, 保存到路径

    # 找色
    # target_color = '#1F2430'
    # source_color = window.get_pixel_color(x=100, y=100)
    # result, sim = window.match_color(
    #     target_color=target_color,
    #     source_color=source_color,
    #     similarity=0.8,
    # )
    # print(result, sim)

    # 找图
    # image = window.read_image(r'img\4.png')
    # (x, y), sim = window.match_image(
    #     target_image=image,
    #     rect=None,      # 搜索区域，默认全窗口
    #     # rect=(100, 100, 200, 200),
    #     similarity=0.8,
    # )
    # print(x, y, sim)

    # 图像预处理
    # image = window.read_image(r"examples\text.png")
    # image = window.proc_image(image, colors=["#1A1A1A", "#AC1515"], threshold=200)
    # window.save_image(image, r"examples\text_proc.png")

if __name__ == '__main__':
    window_match()