"""
return False 只监听事件，不阻止事件传播
return True 监听事件，并阻止事件传播，可以理解为下一个窗口不会收到该事件
"""

import time
from autoxkit.mousekey import HookListener, KeyEvent, MouseEvent

def key_down(event: KeyEvent):
    print(event.action, event.key_code, event.key_name)
    if event.key_name == 'A':
        print("A键将被阻止传播，其他窗口将无法接收到该事件")
        return True
    return False

def key_up(event: KeyEvent):
    print(event.action, event.key_code, event.key_name)
    return False

def mouse_down(event: MouseEvent):
    print(event.action, event.button, event.position)
    return False

def mouse_up(event: MouseEvent):
    print(event.action, event.button, event.position)
    return False


hook_listener = HookListener()
hook_listener.add_handler('keydown', key_down)
hook_listener.add_handler('keyup', key_up)
hook_listener.add_handler('mousedown', mouse_down)
hook_listener.add_handler('mouseup', mouse_up)
hook_listener.start()

if __name__ == '__main__':
    print("当前鼠标位置:", hook_listener.get_mouse_position())
    print("HookListener 正在运行... 按 Ctrl+C 退出")

    try:
        while True:
            time.sleep(1)
    except Exception:
        hook_listener.stop()