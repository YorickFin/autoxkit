"""Async stream readers and writers for scrcpy-server v4.0."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from . import control
from .binary import (
    ProtocolError,
    StreamConfigurationError,
    StreamDisabledError,
    read_exact,
    read_u32be,
    read_u64be,
)
from .models import AudioVideoEvent, CodecId, DeviceMessage, MediaPacket, StreamKind, VideoSession

DEVICE_NAME_FIELD_LENGTH = 64
PACKET_HEADER_SIZE = 12
PACKET_FLAG_SESSION = 1 << 63
PACKET_FLAG_CONFIG = 1 << 62
PACKET_FLAG_KEY_FRAME = 1 << 61
PACKET_PTS_MASK = PACKET_FLAG_KEY_FRAME - 1


class BaseMediaStream:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, kind: StreamKind) -> None:
        self.reader = reader
        self.writer = writer
        self.kind = kind
        self.codec: CodecId | None = None

    async def read_codec(self) -> CodecId:
        raw = read_u32be(await read_exact(self.reader, 4))
        if raw == 0:
            raise StreamDisabledError(f"{self.kind.value} stream disabled by device")
        if raw == 1:
            raise StreamConfigurationError(f"{self.kind.value} stream configuration error on device")
        try:
            codec = CodecId(raw)
        except ValueError as exc:
            raise ProtocolError(f"unknown codec id: 0x{raw:08x}") from exc
        self.codec = codec
        return codec

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()

    async def _read_media_packet(self) -> MediaPacket:
        if self.codec is None:
            await self.read_codec()
        assert self.codec is not None
        header = await read_exact(self.reader, PACKET_HEADER_SIZE)
        if header[0] & 0x80:
            raise ProtocolError("unexpected video session packet on media stream")
        pts_flags = read_u64be(header, 0)
        size = read_u32be(header, 8)
        if size <= 0:
            raise ProtocolError("invalid media packet size: 0")
        payload = await read_exact(self.reader, size)
        config = bool(pts_flags & PACKET_FLAG_CONFIG)
        key_frame = bool(pts_flags & PACKET_FLAG_KEY_FRAME)
        pts = None if config else pts_flags & PACKET_PTS_MASK
        return MediaPacket(self.kind, self.codec, payload, pts, config, key_frame)


class VideoStream(BaseMediaStream):
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        merge_config_packets: bool = True,
    ) -> None:
        super().__init__(reader, writer, StreamKind.VIDEO)
        self.session: VideoSession | None = None
        self.merge_config_packets = merge_config_packets
        self._pending_config: bytes | None = None

    async def read_session(self) -> VideoSession:
        if self.codec is None:
            await self.read_codec()
        header = await read_exact(self.reader, PACKET_HEADER_SIZE)
        if not header[0] & 0x80:
            raise ProtocolError("expected video session packet")
        session = VideoSession(
            width=read_u32be(header, 4),
            height=read_u32be(header, 8),
            client_resized=bool(header[3] & 1),
        )
        self.session = session
        return session

    async def events(self) -> AsyncIterator[AudioVideoEvent]:
        codec = await self.read_codec()
        session = await self.read_session()
        yield AudioVideoEvent(kind=StreamKind.SESSION, codec=codec, session=session)

        while True:
            try:
                header = await read_exact(self.reader, PACKET_HEADER_SIZE)
            except EOFError:
                return
            if header[0] & 0x80:
                session = VideoSession(
                    width=read_u32be(header, 4),
                    height=read_u32be(header, 8),
                    client_resized=bool(header[3] & 1),
                )
                self.session = session
                yield AudioVideoEvent(kind=StreamKind.SESSION, codec=codec, session=session)
                continue

            packet = await self._packet_from_header(header)
            if self.merge_config_packets and codec in {CodecId.H264, CodecId.H265}:
                packet = self._merge_config(packet)
                if packet is None:
                    continue
            yield AudioVideoEvent(
                kind=StreamKind.VIDEO,
                codec=packet.codec,
                payload=packet.payload,
                pts=packet.pts,
                config=packet.config,
                key_frame=packet.key_frame,
            )

    async def packets(self) -> AsyncIterator[MediaPacket]:
        async for event in self.events():
            if event.kind is StreamKind.VIDEO:
                assert event.codec is not None
                yield MediaPacket(event.kind, event.codec, event.payload, event.pts, event.config, event.key_frame)

    async def _packet_from_header(self, header: bytes) -> MediaPacket:
        assert self.codec is not None
        pts_flags = read_u64be(header, 0)
        size = read_u32be(header, 8)
        if size <= 0:
            raise ProtocolError("invalid video packet size: 0")
        payload = await read_exact(self.reader, size)
        config = bool(pts_flags & PACKET_FLAG_CONFIG)
        key_frame = bool(pts_flags & PACKET_FLAG_KEY_FRAME)
        pts = None if config else pts_flags & PACKET_PTS_MASK
        return MediaPacket(StreamKind.VIDEO, self.codec, payload, pts, config, key_frame)

    def _merge_config(self, packet: MediaPacket) -> MediaPacket | None:
        if packet.config:
            self._pending_config = packet.payload
            return None
        if self._pending_config:
            packet = MediaPacket(
                packet.kind,
                packet.codec,
                self._pending_config + packet.payload,
                packet.pts,
                packet.config,
                packet.key_frame,
            )
            self._pending_config = None
        return packet


class AudioStream(BaseMediaStream):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        super().__init__(reader, writer, StreamKind.AUDIO)

    async def packets(self) -> AsyncIterator[MediaPacket]:
        await self.read_codec()
        while True:
            try:
                yield await self._read_media_packet()
            except EOFError:
                return

    async def events(self) -> AsyncIterator[AudioVideoEvent]:
        async for packet in self.packets():
            yield AudioVideoEvent(
                kind=StreamKind.AUDIO,
                codec=packet.codec,
                payload=packet.payload,
                pts=packet.pts,
                config=packet.config,
                key_frame=packet.key_frame,
            )


class ControlStream:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.reader = reader
        self.writer = writer
        self._device_buffer = bytearray()

    async def send(self, message: control.ControlMessage) -> None:
        self.writer.write(message.payload)
        await self.writer.drain()

    async def send_keycode(self, action: int, keycode: int, repeat: int = 0, metastate: int = 0) -> None:
        await self.send(control.inject_keycode(action, keycode, repeat, metastate))

    async def send_touch(
        self,
        action: int,
        x: int,
        y: int,
        screen_width: int,
        screen_height: int,
        pointer_id: int = control.POINTER_ID_GENERIC_FINGER,
        pressure: float = 1.0,
        action_button: int = 0,
        buttons: int = 0,
    ) -> None:
        position = control.Position(x, y, screen_width, screen_height)
        await self.send(control.inject_touch_event(action, position, pointer_id, pressure, action_button, buttons))

    async def set_clipboard(self, text: str, sequence: int = 1, paste: bool = False) -> None:
        await self.send(control.set_clipboard(sequence, text, paste))

    async def device_messages(self) -> AsyncIterator[DeviceMessage]:
        while True:
            chunk = await self.reader.read(4096)
            if not chunk:
                return
            self._device_buffer.extend(chunk)
            while True:
                msg, consumed = control.deserialize_device_message(bytes(self._device_buffer))
                if consumed == 0:
                    break
                del self._device_buffer[:consumed]
                assert msg is not None
                yield msg

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()


class AudioVideoCombinedStream:
    """A local virtual stream merging video and audio events from official sockets."""

    def __init__(self, video: VideoStream | None, audio: AudioStream | None) -> None:
        self.video = video
        self.audio = audio

    async def events(self) -> AsyncIterator[AudioVideoEvent]:
        queue: asyncio.Queue[AudioVideoEvent | BaseException | None] = asyncio.Queue()
        tasks: list[asyncio.Task[None]] = []

        async def pump(source: AsyncIterator[AudioVideoEvent]) -> None:
            try:
                async for event in source:
                    await queue.put(event)
            except (EOFError, asyncio.IncompleteReadError):
                pass
            except BaseException as exc:
                await queue.put(exc)
            finally:
                await queue.put(None)

        if self.video is not None:
            tasks.append(asyncio.create_task(pump(self.video.events())))
        if self.audio is not None:
            tasks.append(asyncio.create_task(pump(self.audio.events())))
        if not tasks:
            return

        completed = 0
        try:
            while completed < len(tasks):
                item = await queue.get()
                if item is None:
                    completed += 1
                elif isinstance(item, BaseException):
                    raise item
                else:
                    yield item
        finally:
            for task in tasks:
                task.cancel()
