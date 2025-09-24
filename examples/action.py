import time
from autoxkit import MouseControl, KeyBoardControl

def mouse_action():
    mousecontrol = MouseControl()
    mousecontrol.mouse_move(500, 500)
    mousecontrol.left_down()
    time.sleep(0.04)
    mousecontrol.left_up()

    time.sleep(1)

    mousecontrol.mouse_move(600, 600)
    mousecontrol.left_click()

def keyboard_action():
    keyboardcontrol = KeyBoardControl()
    keyboardcontrol.key_down('A')
    time.sleep(0.04)
    keyboardcontrol.key_up('A')

    keyboardcontrol.key_click('B')


if __name__ == '__main__':
    mouse_action()
    keyboard_action()