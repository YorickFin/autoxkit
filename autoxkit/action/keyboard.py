import ctypes
import time

# 键盘按键码
Hex_key_code = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46, "G": 0x47,
    "H": 0x48, "I": 0x49, "J": 0x4a, "K": 0x4b, "L": 0x4c, "M": 0x4d, "N": 0x4e,
    "O": 0x4f, "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54, "U": 0x55,
    "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59, "Z": 0x5a, "Space": 0x20,
    "Oem_4": 0xdb, "Oem_6": 0xdd, "Oem_1": 0xba, "Oem_7": 0xde, "Oem_Comma": 0xbc,
    "Oem_Period": 0xbe, "Oem_2": 0xbf, "Oem_5": 0xdc, "Oem_3": 0xc0, "0": 0x30,
    "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34, "5": 0x35, "6": 0x36, "7": 0x37,
    "8": 0x38, "9": 0x39, "Oem_Minus": 0xbd, "Oem_Plus": 0xbb, "Numpad0": 0x60,
    "Numpad1": 0x61, "Numpad2": 0x62, "Numpad3": 0x63, "Numpad4": 0x64, "Numpad5": 0x65,
    "Numpad6": 0x66, "Numpad7": 0x67, "Numpad8": 0x68, "Numpad9": 0x69, "Decimal": 0x6e,
    "Add": 0x6b, "Subtract": 0x6d, "Multiply": 0x6a, "Divide": 0x6f, "Numlock": 0x90,
    "Return": 0x0D, "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74,
    "F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A,
    "F12": 0x7B, "Back": 0x08, "Tab": 0x09, "Lshift": 0xA0, "Rshift": 0xA1,
    "Lctrl": 0xA2, "Rctrl": 0xA3, "Capital": 0x14, "Lalt": 0xA4, "Ralt": 0xA5,
    "Lwin": 0x5B, "Rwin": 0x5C, "Apps": 0x5D, "Escape": 0x1B, "Insert": 0x2D,
    "Delete": 0x2E, "Home": 0x24, "End": 0x23, "Prior": 0x21, "Next": 0x22,
    "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28, "Volume_Down": 0xAE,
    "Volume_Up": 0xAF, "Volume_Mute": 0xAD, "Launch_App2": 0xB7,
}

def key_down(key_name: str):
    """模拟按下按键"""
    ctypes.windll.user32.keybd_event(Hex_key_code[key_name], 0, 0, 0)

def key_up(key_name: str):
    """模拟释放按键"""
    ctypes.windll.user32.keybd_event(Hex_key_code[key_name], 0, 2, 0)

def key_click(key_name: str, duration=0.04):
    """模拟单击按键"""
    key_down(key_name)
    time.sleep(duration)
    key_up(key_name)

def key_combination(keys: list, duration=0.1):
    """模拟组合键"""

    for key_name in keys:
        key_down(key_name)
        time.sleep(0.04)

    # 保持组合键状态
    time.sleep(duration)

    for key_name in reversed(keys):
        key_up(key_name)
        time.sleep(0.04)