import time
from autoxkit import Mouse, KeyBoard

def mouse_action():
    mouse = Mouse()
    mouse.mouse_move(500, 500)
    mouse.left_down()
    time.sleep(0.04)
    mouse.left_up()

    time.sleep(1)

    mouse.mouse_move(600, 600)
    mouse.left_click()

def keyboard_action():
    time.sleep(3)
    keyboard = KeyBoard()
    keyboard.key_down('A')
    time.sleep(0.01)
    keyboard.key_up('A')

    keyboard.key_click('B')


if __name__ == '__main__':
    # mouse_action()
    keyboard_action()