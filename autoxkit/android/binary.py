"""scrcpy v4.0 协议的二进制辅助函数。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


ReadExact = Callable[[int], Awaitable[bytes]]


class ProtocolError(Exception):
    """当网络上的字节不符合预期协议时抛出。"""


class StreamDisabledError(ProtocolError):
    """当 scrcpy-server 显式禁用媒体流时抛出。"""


class StreamConfigurationError(ProtocolError):
    """当 scrcpy-server 报告媒体流配置错误时抛出。"""


def u16be(value: int) -> bytes:
    return int(value).to_bytes(2, "big", signed=False)


def i16be(value: int) -> bytes:
    return int(value).to_bytes(2, "big", signed=True)


def u32be(value: int) -> bytes:
    return int(value).to_bytes(4, "big", signed=False)


def i32be(value: int) -> bytes:
    return int(value).to_bytes(4, "big", signed=True)


def u64be(value: int) -> bytes:
    return int(value).to_bytes(8, "big", signed=False)


def read_u16be(data: bytes | bytearray | memoryview, offset: int = 0) -> int:
    return int.from_bytes(data[offset : offset + 2], "big", signed=False)


def read_i16be(data: bytes | bytearray | memoryview, offset: int = 0) -> int:
    return int.from_bytes(data[offset : offset + 2], "big", signed=True)


def read_u32be(data: bytes | bytearray | memoryview, offset: int = 0) -> int:
    return int.from_bytes(data[offset : offset + 4], "big", signed=False)


def read_i32be(data: bytes | bytearray | memoryview, offset: int = 0) -> int:
    return int.from_bytes(data[offset : offset + 4], "big", signed=True)


def read_u64be(data: bytes | bytearray | memoryview, offset: int = 0) -> int:
    return int.from_bytes(data[offset : offset + 8], "big", signed=False)


async def read_exact(reader: asyncio.StreamReader, size: int) -> bytes:
    try:
        return await reader.readexactly(size)
    except asyncio.IncompleteReadError as exc:
        raise EOFError(f"期望 {size} 字节，实际获取 {len(exc.partial)} 字节") from exc


def utf8_truncate(text: str, max_bytes: int) -> bytes:
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return raw
    end = max_bytes
    while end > 0:
        try:
            return raw[:end].decode("utf-8").encode("utf-8")
        except UnicodeDecodeError:
            end -= 1
    return b""


def string32(text: str, max_payload_len: int) -> bytes:
    raw = utf8_truncate(text, max_payload_len)
    return u32be(len(raw)) + raw


def string8(text: str, max_payload_len: int = 255) -> bytes:
    if max_payload_len > 255:
        raise ValueError("1字节字符串不能超过255字节")
    raw = utf8_truncate(text, max_payload_len)
    return bytes([len(raw)]) + raw


def float_to_u16fp(value: float) -> int:
    clamped = max(0.0, min(1.0, value))
    return int(round(clamped * 0xFFFF))


def float_to_i16fp(value: float) -> int:
    clamped = max(-1.0, min(1.0, value))
    if clamped == 1.0:
        return 0x7FFF
    return int(round(clamped * 0x8000))


def u16fp_to_float(value: int) -> float:
    return value / 0xFFFF


def i16fp_to_float(value: int) -> float:
    if value & 0x8000:
        value -= 0x10000
    return value / 0x8000
