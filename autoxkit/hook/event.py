from ..constants import Hex_Key_Code

# 预构建 vkCode → name 反向字典
_VK_TO_NAME = {v: k for k, v in Hex_Key_Code.items()}

class KeyEvent:
    """
        键盘事件
    Args:
        action (str): 事件类型，"keydown"或"keyup"
        vk_code : 按键的16进制虚拟键码
    Attributes:
        action (str): 事件类型，"keydown"或"keyup"
        key_code : 按键的16进制虚拟键码
        key_name (str): 按键名称，例如"Ctrl"、"A" 等
    """
    def __init__(self, action, vk_code):
        self.action = action
        self.key_code = vk_code
        self.key_name = _VK_TO_NAME.get(vk_code, str(vk_code))

class MouseEvent:
    """
        鼠标事件
    Args:
        action (str): 事件类型，"MouseDown"、"MouseUp"或"MouseMove"
        button (str): 鼠标按键，"MLeft"、"MRight"、"Middle"、"MSide1"、"MSide2"、
                      "MUWheel"或"MDWheel"，MouseMove时为None
        x (int): 鼠标x坐标
        y (int): 鼠标y坐标
        distance (int): 滚轮滚动距离，正值为向上滚动，负值为向下滚动。非滚轮事件时为0
    Attributes:
        action (str): 事件类型，"MouseDown"、"MouseUp"或"MouseMove"
        button (str): 鼠标按键，"MLeft"、"MRight"、"Middle"、"MSide1"、"MSide2"、
                      "MUWheel"或"MDWheel"，MouseMove时为None
        position (tuple): 鼠标位置，(x, y)格式
        distance (int): 滚轮滚动距离，正值为向上滚动，负值为向下滚动。非滚轮事件时为0
    """
    def __init__(self, action, button, x, y, distance=0):
        self.action = action
        self.button = button
        self.position = (x, y)
        self.distance = distance
