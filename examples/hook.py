
import time
from autoxkit.mousekey import (set_event_handlers, start_listening, stop_listening,
                               get_mouse_position, KeyEvent, MouseEvent)


# 获取鼠标位置
print(get_mouse_position())

def key_down(event: KeyEvent):
    print('keydown', event.key_name)

def key_up(event: KeyEvent):
    print('keyup', event.key_name)

def mouse_down(event: MouseEvent):
    print('mousedown', event.button, event.position)

def mouse_up(event: MouseEvent):
    print('mouseup', event.button, event.position)

# 注册自定义回调
set_event_handlers(
    on_keydown=key_down,
    on_keyup=key_up,
    on_mousedown=mouse_down,
    on_mouseup=mouse_up,
)

if __name__ == '__main__':
    # 启动监听
    start_listening()
    while True:
        time.sleep(1)


