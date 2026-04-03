from autoxkit import Mouse, KeyBoard


def mouse_action():
    mouse = Mouse()
    mouse.left_click()

def keyboard_action():
    keyboard = KeyBoard()
    # 兼容模式
    # keyboard = KeyBoard(compat=True)
    keyboard.key_click("A")

if __name__ == '__main__':
    mouse_action()
    # keyboard_action()

