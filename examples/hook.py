
import time
from autoxkit.mousekey import HookListener, KeyEvent, MouseEvent

def key_down(event: KeyEvent):
    print('keydown', event.key_name)

def key_up(event: KeyEvent):
    print('keyup', event.key_name)

def mouse_down(event: MouseEvent):
    print('mousedown', event.button, event.position)

def mouse_up(event: MouseEvent):
    print('mouseup', event.button, event.position)


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