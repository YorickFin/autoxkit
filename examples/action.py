import time
from autoxkit import move_absolute, left_down, left_up, left_click, key_down, key_up, key_click

def mouse_action():
    move_absolute(500, 500)
    left_down()
    time.sleep(0.04)
    left_up()

    move_absolute(600, 600)
    left_click()

def keyboard_action():
    key_down('A')
    time.sleep(0.04)
    key_up('A')

    key_click('B')


if __name__ == '__main__':
    mouse_action()
    keyboard_action()