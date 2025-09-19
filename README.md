# autoxkit

[![PyPI version](https://img.shields.io/pypi/v/autoxkit.svg)](https://pypi.org/project/autoxkit/)
[![Python Version](https://img.shields.io/pypi/pyversions/autoxkit.svg)](https://pypi.org/project/autoxkit/)
[![License](https://img.shields.io/github/license/YorickFin/autoxkit)](https://github.com/YorickFin/autoxkit)

一个轻量级的 Windows 自动化库，支持鼠标与键盘操作模拟、全局钩子监听、事件回调机制等功能。适用于自动化脚本、软件测试、人机交互等多种场景。

---

## ✨ 功能特色

- ✅ 全局鼠标和键盘钩子监听
- ✅ 支持鼠标点击、移动、滚轮等操作
- ✅ 支持按键按下、释放、文本输入等模拟
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

import time
from autoxkit import set_event_handlers, start_listening, stop_listening, get_mouse_position

# 获取鼠标位置
print(get_mouse_position())

def key_down(event):
    print('keydown', event.key_name)

def key_up(event):
    print('keyup', event.key_name)

def mouse_down(event):
    print('mousedown', event.button, event.position)

def mouse_up(event):
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
```

更多示例请参考：[examples](https://github.com/YorickFin/autoxkit/tree/main/examples)

---

## 📁 GitHub 项目地址

[👉 https://github.com/YorickFin/autoxkit](https://github.com/YorickFin/autoxkit)

---

## 📃 License

本项目基于 GPL-3.0 许可证开源，欢迎使用与二次开发。