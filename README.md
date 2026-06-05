# autoxkit

[![PyPI version](https://img.shields.io/pypi/v/autoxkit.svg)](https://pypi.org/project/autoxkit/)
[![Python Version](https://img.shields.io/pypi/pyversions/autoxkit.svg)](https://pypi.org/project/autoxkit/)
[![License](https://img.shields.io/github/license/YorickFin/autoxkit)](https://github.com/YorickFin/autoxkit)

一个轻量级的 python 自动化库，支持 Windows 前后台键鼠操作、图像识别、全局 hook 监听等，Android 模块基于 scrcpy-server v4.0 协议支持 Android 无线/有线投屏、键鼠映射等功能。
适用于自动化脚本、软件测试、人机交互等多种场景。

***

## 功能特色

- 前后台键鼠操作
- 前后台图像识别
- 文本输入模拟
- 全局键鼠 hook 监听
- Android 无线/有线投屏
- Android 键鼠映射

Android 模块依赖于 scrcpy v4.0 ，请自行前往 [scrcpy v4.0](https://github.com/Genymobile/scrcpy/releases/tag/v4.0) 下载 scrcpy-win64-v4.0.zip 文件。

***

## 安装方式

从 PyPI 安装：

```bash
pip install autoxkit
```

或下载源码后本地安装：

```bash
pip install .
```

***

## 示例代码
```python
"""
return Any or not return 只监听事件，不阻止事件传播

return True 监听事件，并阻止事件传播，可以理解为下一个窗口不会收到该事件
"""

from autoxkit.hook import HookListener, KeyEvent, MouseEvent

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


def mouse_move(event: MouseEvent):
    print(event.action, event.button, event.position)
    return False


hook_listener = HookListener()
hook_listener.add_handler('keydown', key_down)
hook_listener.add_handler('keyup', key_up)
hook_listener.add_handler('mousedown', mouse_down)
hook_listener.add_handler('mouseup', mouse_up)
hook_listener.add_handler('mousemove', mouse_move)
hook_listener.start()

print("当前鼠标位置:", hook_listener.get_mouse_position())

if __name__ == '__main__':
    try:
        hook_listener.wait()
    except Exception:
        hook_listener.stop()

```

更多示例代码请参考 [examples](examples)

***

## GitHub 项目地址

<https://github.com/YorickFin/autoxkit>

***

## License

本项目基于 GPL-3.0 许可开源，欢迎使用与二次开发。
