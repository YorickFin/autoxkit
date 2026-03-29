import time
from autoxkit.window import Window

def window_action():
    """键鼠操作"""
    # 绑定窗口
    window = Window(title_name='MuMuNxDevice', class_name=None, hand=None)
    # 窗口为后台, 需要先激活窗口
    window.activate_window()

    # 详细按键名自行查看autoxkit.constants.py文件
    # 按键 按下和释放
    # window.send_key_down("A")
    # time.sleep(0.02)
    # window.send_key_up("A")

    # 按键 点击
    # window.send_key_click("A")

    # 按键 组合键
    # window.send_key_combination(["Lctrl", "A"])

    # 鼠标 按下和释放 [left, right, middle]
    # window.send_left_down(100, 100)
    # time.sleep(0.02)
    # window.send_left_up()

    # 鼠标 点击 [left, right, middle]
    # window.send_left_click(100, 100)

    # 鼠标 滚轮滚动
    # window.send_mouse_wheel(100)
    # window.send_mouse_wheel(-100)

    # 发送文字, 需要先点击输入框
    # window.send_left_click(167, 56)
    # time.sleep(1)
    # window.send_left_click(167, 56)
    # time.sleep(1)
    # window.send_text("hello, World!")

if __name__ == "__main__":
    window_action()
