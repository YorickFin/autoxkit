from autoxkit.mousekey import Mouse, KeyBoard


def mouse_action():
    mouse = Mouse()
    mouse.mouse_click(x=1270, y=540, button=0)
    mouse.mouse_click(button=0)     # 沿用最后一个鼠标位置
    mouse.mouse_click(x=-1, y=-1, button=0)     # 使用当前鼠标位置

def keyboard_action():
    keyboard = KeyBoard()
    # 兼容模式
    # keyboard = KeyBoard(compat=True)
    keyboard.key_combination(["RShift", "Oem11"])

if __name__ == '__main__':
    mouse_action()
    # keyboard_action()

