"""scrcpy-server v4.0 的协议数据模型。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class StreamKind(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    SESSION = "session"


class CodecId(IntEnum):
    H264 = 0x68323634
    H265 = 0x68323635
    AV1 = 0x00617631
    OPUS = 0x6F707573
    AAC = 0x00616163
    FLAC = 0x666C6163
    RAW = 0x00726177

    @property
    def label(self) -> str:
        raw = int(self).to_bytes(4, "big")
        return raw.replace(b"\x00", b"").decode("ascii")

    @property
    def is_video(self) -> bool:
        return self in {CodecId.H264, CodecId.H265, CodecId.AV1}

    @property
    def is_audio(self) -> bool:
        return self in {CodecId.OPUS, CodecId.AAC, CodecId.FLAC, CodecId.RAW}


@dataclass(frozen=True, slots=True)
class DeviceMeta:
    device_name: str


@dataclass(frozen=True, slots=True)
class VideoSession:
    width: int
    height: int
    client_resized: bool = False


@dataclass(frozen=True, slots=True)
class MediaPacket:
    kind: StreamKind
    codec: CodecId
    payload: bytes
    pts: int | None
    config: bool = False
    key_frame: bool = False


@dataclass(frozen=True, slots=True)
class AudioVideoEvent:
    kind: StreamKind
    codec: CodecId | None
    payload: bytes = b""
    pts: int | None = None
    config: bool = False
    key_frame: bool = False
    session: VideoSession | None = None


class ControlMessageType(IntEnum):
    INJECT_KEYCODE = 0
    INJECT_TEXT = 1
    INJECT_TOUCH_EVENT = 2
    INJECT_SCROLL_EVENT = 3
    BACK_OR_SCREEN_ON = 4
    EXPAND_NOTIFICATION_PANEL = 5
    EXPAND_SETTINGS_PANEL = 6
    COLLAPSE_PANELS = 7
    GET_CLIPBOARD = 8
    SET_CLIPBOARD = 9
    SET_DISPLAY_POWER = 10
    ROTATE_DEVICE = 11
    UHID_CREATE = 12
    UHID_INPUT = 13
    UHID_DESTROY = 14
    OPEN_HARD_KEYBOARD_SETTINGS = 15
    START_APP = 16
    RESET_VIDEO = 17
    CAMERA_SET_TORCH = 18
    CAMERA_ZOOM_IN = 19
    CAMERA_ZOOM_OUT = 20
    RESIZE_DISPLAY = 21


class DeviceMessageType(IntEnum):
    CLIPBOARD = 0
    ACK_CLIPBOARD = 1
    UHID_OUTPUT = 2


@dataclass(frozen=True, slots=True)
class Position:
    x: int
    y: int
    screen_width: int
    screen_height: int


@dataclass(frozen=True, slots=True)
class ControlMessage:
    type: ControlMessageType
    payload: bytes


@dataclass(frozen=True, slots=True)
class DeviceMessage:
    type: DeviceMessageType
    text: str | None = None
    sequence: int | None = None
    uhid_id: int | None = None
    data: bytes | None = None
