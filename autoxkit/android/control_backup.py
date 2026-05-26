"""scrcpy-server v4.0 的控制消息和设备消息序列化器。"""

from __future__ import annotations

from .binary import (
    ProtocolError,
    float_to_i16fp,
    float_to_u16fp,
    i16be,
    i32be,
    read_u16be,
    read_u32be,
    read_u64be,
    string8,
    string32,
    u16be,
    u32be,
    u64be,
)
from .models import ControlMessage, ControlMessageType, DeviceMessage, DeviceMessageType, Position

MESSAGE_MAX_SIZE = 1 << 18
INJECT_TEXT_MAX_LENGTH = 300
CLIPBOARD_TEXT_MAX_LENGTH = MESSAGE_MAX_SIZE - 14

ACTION_DOWN = 0
ACTION_UP = 1
ACTION_MOVE = 2

POINTER_ID_MOUSE = -1 & 0xFFFFFFFFFFFFFFFF
POINTER_ID_GENERIC_FINGER = -2 & 0xFFFFFFFFFFFFFFFF


def _position(position: Position) -> bytes:
    return (
        i32be(position.x)
        + i32be(position.y)
        + u16be(position.screen_width)
        + u16be(position.screen_height)
    )


def inject_keycode(action: int, keycode: int, repeat: int = 0, metastate: int = 0) -> ControlMessage:
    payload = (
        bytes([ControlMessageType.INJECT_KEYCODE, action])
        + i32be(keycode)
        + u32be(repeat)
        + u32be(metastate)
    )
    return ControlMessage(ControlMessageType.INJECT_KEYCODE, payload)


def inject_text(text: str) -> ControlMessage:
    payload = bytes([ControlMessageType.INJECT_TEXT]) + string32(text, INJECT_TEXT_MAX_LENGTH)
    return ControlMessage(ControlMessageType.INJECT_TEXT, payload)


def inject_touch_event(
    action: int,
    position: Position,
    pointer_id: int = POINTER_ID_GENERIC_FINGER,
    pressure: float = 1.0,
    action_button: int = 0,
    buttons: int = 0,
) -> ControlMessage:
    payload = (
        bytes([ControlMessageType.INJECT_TOUCH_EVENT, action])
        + u64be(pointer_id)
        + _position(position)
        + u16be(float_to_u16fp(pressure))
        + u32be(action_button)
        + u32be(buttons)
    )
    return ControlMessage(ControlMessageType.INJECT_TOUCH_EVENT, payload)


def inject_scroll_event(position: Position, hscroll: float = 0.0, vscroll: float = 0.0, buttons: int = 0) -> ControlMessage:
    h = float_to_i16fp(hscroll / 16)
    v = float_to_i16fp(vscroll / 16)
    payload = (
        bytes([ControlMessageType.INJECT_SCROLL_EVENT])
        + _position(position)
        + i16be(h)
        + i16be(v)
        + u32be(buttons)
    )
    return ControlMessage(ControlMessageType.INJECT_SCROLL_EVENT, payload)


def back_or_screen_on(action: int) -> ControlMessage:
    return ControlMessage(ControlMessageType.BACK_OR_SCREEN_ON, bytes([ControlMessageType.BACK_OR_SCREEN_ON, action]))


def get_clipboard(copy_key: int = 0) -> ControlMessage:
    return ControlMessage(ControlMessageType.GET_CLIPBOARD, bytes([ControlMessageType.GET_CLIPBOARD, copy_key]))


def set_clipboard(sequence: int, text: str, paste: bool = False) -> ControlMessage:
    payload = (
        bytes([ControlMessageType.SET_CLIPBOARD])
        + u64be(sequence)
        + bytes([1 if paste else 0])
        + string32(text, CLIPBOARD_TEXT_MAX_LENGTH)
    )
    return ControlMessage(ControlMessageType.SET_CLIPBOARD, payload)


def set_display_power(on: bool) -> ControlMessage:
    return ControlMessage(ControlMessageType.SET_DISPLAY_POWER, bytes([ControlMessageType.SET_DISPLAY_POWER, int(on)]))


def empty(message_type: ControlMessageType) -> ControlMessage:
    if message_type not in {
        ControlMessageType.EXPAND_NOTIFICATION_PANEL,
        ControlMessageType.EXPAND_SETTINGS_PANEL,
        ControlMessageType.COLLAPSE_PANELS,
        ControlMessageType.ROTATE_DEVICE,
        ControlMessageType.OPEN_HARD_KEYBOARD_SETTINGS,
        ControlMessageType.RESET_VIDEO,
        ControlMessageType.CAMERA_ZOOM_IN,
        ControlMessageType.CAMERA_ZOOM_OUT,
    }:
        raise ValueError(f"{message_type.name} 不是空控制消息")
    return ControlMessage(message_type, bytes([message_type]))


def camera_set_torch(on: bool) -> ControlMessage:
    return ControlMessage(ControlMessageType.CAMERA_SET_TORCH, bytes([ControlMessageType.CAMERA_SET_TORCH, int(on)]))


def resize_display(width: int, height: int) -> ControlMessage:
    payload = bytes([ControlMessageType.RESIZE_DISPLAY]) + u16be(width) + u16be(height)
    return ControlMessage(ControlMessageType.RESIZE_DISPLAY, payload)


def start_app(name: str) -> ControlMessage:
    payload = bytes([ControlMessageType.START_APP]) + string8(name, 255)
    return ControlMessage(ControlMessageType.START_APP, payload)


def uhid_create(uhid_id: int, vendor_id: int, product_id: int, name: str, report_desc: bytes) -> ControlMessage:
    payload = (
        bytes([ControlMessageType.UHID_CREATE])
        + u16be(uhid_id)
        + u16be(vendor_id)
        + u16be(product_id)
        + string8(name, 127)
        + u16be(len(report_desc))
        + report_desc
    )
    return ControlMessage(ControlMessageType.UHID_CREATE, payload)


def uhid_input(uhid_id: int, data: bytes) -> ControlMessage:
    payload = bytes([ControlMessageType.UHID_INPUT]) + u16be(uhid_id) + u16be(len(data)) + data
    return ControlMessage(ControlMessageType.UHID_INPUT, payload)


def uhid_destroy(uhid_id: int) -> ControlMessage:
    return ControlMessage(ControlMessageType.UHID_DESTROY, bytes([ControlMessageType.UHID_DESTROY]) + u16be(uhid_id))


def deserialize_device_message(buffer: bytes) -> tuple[DeviceMessage | None, int]:
    if not buffer:
        return None, 0
    try:
        message_type = DeviceMessageType(buffer[0])
    except ValueError as exc:
        raise ProtocolError(f"未知的设备消息类型: {buffer[0]}") from exc

    if message_type is DeviceMessageType.CLIPBOARD:
        if len(buffer) < 5:
            return None, 0
        size = read_u32be(buffer, 1)
        total = 5 + size
        if len(buffer) < total:
            return None, 0
        text = buffer[5:total].decode("utf-8")
        return DeviceMessage(message_type, text=text), total

    if message_type is DeviceMessageType.ACK_CLIPBOARD:
        if len(buffer) < 9:
            return None, 0
        return DeviceMessage(message_type, sequence=read_u64be(buffer, 1)), 9

    if len(buffer) < 5:
        return None, 0
    uhid_id = read_u16be(buffer, 1)
    size = read_u16be(buffer, 3)
    total = 5 + size
    if len(buffer) < total:
        return None, 0
    return DeviceMessage(message_type, uhid_id=uhid_id, data=buffer[5:total]), total
