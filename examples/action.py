from autoxkit.mousekey import Mouse, KeyBoard


def mouse_action():
    mouse = Mouse()
    mouse.mouse_click(x=1270, y=540, button=0)

def keyboard_action():
    keyboard = KeyBoard()
    # 兼容模式
    # keyboard = KeyBoard(compat=True)
    keyboard.key_combination(["RShift", "Oem11"])

if __name__ == '__main__':
    mouse_action()
    # keyboard_action()

