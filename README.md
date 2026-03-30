# autoxkit

[![PyPI version](https://img.shields.io/pypi/v/autoxkit.svg)](https://pypi.org/project/autoxkit/)
[![Python Version](https://img.shields.io/pypi/pyversions/autoxkit.svg)](https://pypi.org/project/autoxkit/)
[![License](https://img.shields.io/github/license/YorickFin/autoxkit)](https://github.com/YorickFin/autoxkit)

一个轻量级的 Windows 自动化库，支持前后台键鼠操作、前后台图色识别、全局hook监听等功能。适用于自动化脚本、软件测试、人机交互等多种场景。

---

## ✨ 功能特色

- ✅ 前后台键鼠操作
- ✅ 前后台图色识别
- ✅ 文本输入模拟
- ✅ 全局鼠标和键盘hook监听
- ✅ 简洁的事件回调机制，便于集成和扩展
- ✅ 完全基于 Python 实现，易于上手和二次开发

---

## 📦 安装方式

从 PyPI 安装：

```bash
pip install autoxkit
```

或下载源码后本地安装：

```bash
pip install .
```

---

## 🔧 使用示例

```python
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
```

更多示例请参考：[examples](https://github.com/YorickFin/autoxkit/tree/main/examples)

---

## 📁 GitHub 项目地址

[👉 https://github.com/YorickFin/autoxkit](https://github.com/YorickFin/autoxkit)

---

## 📃 License

本项目基于 GPL-3.0 许可证开源，欢迎使用与二次开发。