from ..constants import Hex_Key_Code

class KeyEvent:
    """
        键盘事件
    Args:
        action (str): 事件类型，"keydown"或"keyup"
        vk_code : 按键的16进制虚拟键码
    Attributes:
        action (str): 事件类型，"keydown"或"keyup"
        key_code : 按键的16进制虚拟键码
        key_name (str): 按键名称，例如 "Ctrl"、"A" 等
    """
    def __init__(self, action, vk_code):
        self.action = action
        self.key_code = vk_code
        name = next((k for k, v in Hex_Key_Code.items() if v == vk_code), None)
        self.key_name = name if name else str(vk_code)

class MouseEvent:
    """
        鼠标事件
    Args:
        action (str): 事件类型，"MouseDown"或"MouseUp"
        button (str): 鼠标按钮，"MLeft"、"MRight"、"MMiddle"、"side1"、"side2"
        x (int): 鼠标x坐标
        y (int): 鼠标y坐标
    Attributes:
        action (str): 事件类型，"MouseDown"或"MouseUp"
        button (str): 鼠标按钮，"MLeft"、"MRight"、"MMiddle"、"side1"、"side2"
        position (tuple): 鼠标位置，(x, y)格式
    """
    def __init__(self, action, button, x, y):
        self.action = action
        self.button = button
        self.position = (x, y)