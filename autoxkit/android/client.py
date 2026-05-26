"""高级 scrcpy-server v4.0 客户端外观类。"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from pathlib import Path

from .adb import AdbServerLauncher
from .binary import read_exact
from .models import DeviceMeta
from .streams import AudioStream, AudioVideoCombinedStream, ControlStream, DEVICE_NAME_FIELD_LENGTH, VideoStream


@dataclass(slots=True)
class ScrcpyOptions:
    """用于启动和连接 scrcpy-server v4.0 的选项。"""

    serial: str | None = None
    adb_path: Path = Path("scrcpy-win64-v4.0") / "adb.exe"
    server_path: Path = Path("scrcpy-win64-v4.0") / "scrcpy-server"
    version: str = "4.0"
    host: str = "127.0.0.1"
    port: int = 0
    scid: int | None = None
    video: bool = True
    audio: bool = True
    control: bool = True
    tunnel_forward: bool = False
    log_level: str = "info"
    push_server: bool = True
    merge_video_config_packets: bool = True
    tcpip: bool = False
    """在启动 scrcpy-server 之前启用 ADB-over-TCP/IP。

    如果设置了 ``tcpip_dst``，客户端运行 ``adb connect`` 连接到该地址，
    并将其用作设备序列号。如果未设置 ``tcpip_dst``，客户端
    假设当前选择了一个 USB 设备，从 ``adb shell ip route`` 读取其 WLAN IP 地址，
    运行 ``adb tcpip <tcpip_port>``，然后连接到 ``<device-ip>:<tcpip_port>``。
    """

    tcpip_dst: str | None = None
    """已知的无线 ADB 地址。

    接受的格式为 ``"192.168.1.23"`` 和 ``"192.168.1.23:5555"``。如果省略端口，
    则会附加 ``tcpip_port``。
    """

    tcpip_port: int = 5555
    """用于 ``adb tcpip`` 和默认地址端口的无线 ADB TCP 端口。"""

    tcpip_disconnect_existing: bool = False
    """在 ``adb connect <address>`` 之前运行 ``adb disconnect <address>``。"""

    server_args: list[str] = field(default_factory=list)
    """传递给 ``scrcpy-server`` 的额外原始 ``key=value`` 参数。

    这些值会附加在 ``ScrcpyClient`` 直接管理的参数之后。除非你也相应地更新了
    Python 端的连接逻辑，否则避免覆盖已管理的键（``scid``、``log_level``、
    ``video``、``audio``、``control`` 和 ``tunnel_forward``）。

    scrcpy-server v4.0 的常见值：

    - ``video_codec``: ``h264``、``h265`` 或 ``av1``。
    - ``audio_codec``: ``opus``、``aac``、``flac`` 或 ``raw``。
    - ``video_source``: ``display`` 或 ``camera``。
    - ``audio_source``: ``output``、``mic``、``playback``、
      ``mic-unprocessed``、``mic-camcorder``、``mic-voice-recognition``、
      ``mic-voice-communication``、``voice-call``、``voice-call-uplink``、
      ``voice-call-downlink`` 或 ``voice-performance``。
    - ``video_bit_rate`` / ``audio_bit_rate``: 整数比特率（单位：比特/秒）。
    - ``max_size``: 整数最大视频尺寸，``0`` 表示无限制。
    - ``max_fps``: 浮点数/整数 FPS 字符串，例如 ``30`` 或 ``60``。
    - ``min_size_alignment``: ``1``、``2``、``4``、``8`` 或 ``16``。
    - ``angle``: 浮点度数字符串。
    - ``crop``: ``width:height:x:y``。
    - ``video_codec_options`` / ``audio_codec_options``:
      逗号分隔的 MediaCodec 选项，``key[:type]=value``。
    - ``video_encoder`` / ``audio_encoder``: Android 编码器名称。
    - ``display_id``: 整数显示 ID。
    - ``new_display``: 空字符串、``widthxheight``、``/dpi`` 或
      ``widthxheight/dpi``。
    - ``flex_display``: 布尔值。
    - ``display_ime_policy``: ``local``、``fallback`` 或 ``hide``。
    - ``vd_destroy_content`` / ``vd_system_decorations``: 布尔值。
    - ``capture_orientation``: 方向名称，可选择以 ``@`` 前缀锁定；``@`` 单独使用锁定初始方向。
    - ``camera_id``: 相机 ID 字符串。
    - ``camera_size``: ``widthxheight``。
    - ``camera_facing``: ``front``、``back`` 或 ``external``。
    - ``camera_ar``: ``sensor``、``width:height`` 或浮点比率。
    - ``camera_fps``: 整数 FPS。
    - ``camera_high_speed`` / ``camera_torch`` / ``audio_dup`` /
      ``show_touches`` / ``stay_awake`` / ``power_off_on_close`` /
      ``clipboard_autosync`` / ``downsize_on_error`` / ``cleanup`` /
      ``power_on`` / ``keep_active``: 布尔值。
    - ``screen_off_timeout``: 整数毫秒，或 ``-1`` 表示不变。
    - ``list_encoders``、``list_displays``、``list_cameras``、
      ``list_camera_sizes`` 和 ``list_apps``: 布尔值列表模式。
    - ``send_device_meta``、``send_frame_meta``、``send_dummy_byte``、
      ``send_stream_meta`` 和 ``raw_stream``: 协议/测试布尔值。

    布尔值传递为 ``true`` 或 ``false``。值必须使用 scrcpy-server v4.0 的选项名称和
    有线格式；此客户端不执行任何验证或 shell 转义。
    """


class ScrcpyClient:
    def __init__(self, options: ScrcpyOptions) -> None:
        if not (options.video or options.audio or options.control):
            raise ValueError("必须至少启用 video、audio 或 control 中的一项")
        self.options = options
        self.scid = options.scid if options.scid is not None else random.getrandbits(31)
        self.socket_name = f"scrcpy_{self.scid:08x}"
        self.launcher = AdbServerLauncher(options.adb_path, options.server_path, options.serial)
        self.device_meta: DeviceMeta | None = None
        self.video: VideoStream | None = None
        self.audio: AudioStream | None = None
        self.control: ControlStream | None = None
        self.av = AudioVideoCombinedStream(None, None)
        self._server_process: asyncio.subprocess.Process | None = None
        self._tcp_server: asyncio.AbstractServer | None = None
        self._accepted: asyncio.Queue[tuple[asyncio.StreamReader, asyncio.StreamWriter]] = asyncio.Queue()
        self._port: int = options.port

    async def start(self) -> None:
        await self._configure_tcpip()
        if self.options.push_server:
            await self.launcher.push_server()

        # 自动检测 TCP/IP（无线）序列号 — ADB reverse 在无线 ADB 上不工作，
        # 因此自动回退到正向隧道。
        if self._is_tcpip_address(self.launcher.serial) and not self.options.tunnel_forward:
            print("检测到 TCP/IP 设备，使用 adb forward 隧道")
            await self._start_forward()
        elif self.options.tunnel_forward:
            await self._start_forward()
        else:
            await self._start_reverse()
        self.av = AudioVideoCombinedStream(self.video, self.audio)

    async def stop(self) -> None:
        streams = [self.video, self.audio, self.control]
        for stream in streams:
            if stream is not None:
                try:
                    await stream.close()
                except OSError:
                    pass
        if self._tcp_server is not None:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()
            self._tcp_server = None
        if self._server_process is not None and self._server_process.returncode is None:
            self._server_process.terminate()
            try:
                await asyncio.wait_for(self._server_process.wait(), timeout=1)
            except TimeoutError:
                self._server_process.kill()
                await self._server_process.wait()
        if self.options.tunnel_forward:
            await self.launcher.remove_forward(self._port)
        else:
            await self.launcher.remove_reverse(self.socket_name)

    async def _configure_tcpip(self) -> None:
        if not self.options.tcpip and not self.options.tcpip_dst:
            return

        if self.options.tcpip_dst:
            address = self._normalize_tcpip_address(self.options.tcpip_dst)
            if self.options.tcpip_disconnect_existing:
                await self.launcher.disconnect_tcpip(address)
            await self.launcher.connect_tcpip(address)
            return

        device_ip = await self.launcher.get_device_ip()
        await self.launcher.enable_tcpip(self.options.tcpip_port)
        await asyncio.sleep(1)
        address = self._normalize_tcpip_address(device_ip)
        if self.options.tcpip_disconnect_existing:
            await self.launcher.disconnect_tcpip(address)
        await self.launcher.connect_tcpip(address)

    def _normalize_tcpip_address(self, address: str) -> str:
        if ":" in address:
            return address
        return f"{address}:{self.options.tcpip_port}"

    @staticmethod
    def _is_tcpip_address(serial: str | None) -> bool:
        """如果序列号看起来像 TCP/IP 地址（ip:port），返回 True。"""
        return serial is not None and ":" in serial

    async def _start_reverse(self) -> None:
        self._tcp_server = await asyncio.start_server(self._on_accept, self.options.host, self.options.port)
        sockets = self._tcp_server.sockets or []
        if not sockets:
            raise RuntimeError("无法创建本地服务器套接字")
        self._port = int(sockets[0].getsockname()[1])
        await self.launcher.reverse(self.socket_name, self._port)
        self._server_process = await self._start_server_process(tunnel_forward=False)
        await self._accept_streams(read_dummy_byte=False)

    async def _start_forward(self) -> None:
        self._port = self.options.port or 27183
        # 首先移除任何陈旧的正向映射以避免冲突
        await self.launcher.remove_forward(self._port)
        await self.launcher.forward(self.socket_name, self._port)
        self._server_process = await self._start_server_process(tunnel_forward=True)
        # 在连接之前给服务器时间创建 LocalServerSocket
        await asyncio.sleep(1)
        await self._connect_streams(read_dummy_byte=True)

    async def _start_server_process(self, tunnel_forward: bool) -> asyncio.subprocess.Process:
        return await self.launcher.start_server_process(
            version=self.options.version,
            scid=self.scid,
            tunnel_forward=tunnel_forward,
            video=self.options.video,
            audio=self.options.audio,
            control=self.options.control,
            log_level=self.options.log_level,
            extra_args=self.options.server_args,
        )

    async def _on_accept(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await self._accepted.put((reader, writer))

    async def _accept_streams(self, read_dummy_byte: bool) -> None:
        pairs = []
        for _ in range(self._expected_socket_count()):
            pairs.append(await asyncio.wait_for(self._accepted.get(), timeout=5))
        await self._assign_streams(pairs, read_dummy_byte)

    async def _connect_streams(self, read_dummy_byte: bool) -> None:
        pairs = []
        for _ in range(self._expected_socket_count()):
            pairs.append(await self._connect_with_retry())
        await self._assign_streams(pairs, read_dummy_byte)

    async def _connect_with_retry(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        last_error: OSError | None = None
        for _ in range(100):
            try:
                return await asyncio.open_connection(self.options.host, self._port)
            except OSError as exc:
                last_error = exc
                await asyncio.sleep(0.1)
        raise ConnectionError(f"无法连接到转发的 scrcpy 套接字: {last_error}")

    async def _assign_streams(
        self,
        pairs: list[tuple[asyncio.StreamReader, asyncio.StreamWriter]],
        read_dummy_byte: bool,
    ) -> None:
        if read_dummy_byte:
            await read_exact(pairs[0][0], 1)
        self.device_meta = await self._read_device_meta(pairs[0][0])

        index = 0
        if self.options.video:
            reader, writer = pairs[index]
            self.video = VideoStream(reader, writer, self.options.merge_video_config_packets)
            index += 1
        if self.options.audio:
            reader, writer = pairs[index]
            self.audio = AudioStream(reader, writer)
            index += 1
        if self.options.control:
            reader, writer = pairs[index]
            self.control = ControlStream(reader, writer)

    async def _read_device_meta(self, reader: asyncio.StreamReader) -> DeviceMeta:
        raw = await read_exact(reader, DEVICE_NAME_FIELD_LENGTH)
        device_name = raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
        return DeviceMeta(device_name)

    def _expected_socket_count(self) -> int:
        return int(self.options.video) + int(self.options.audio) + int(self.options.control)

    async def __aenter__(self) -> ScrcpyClient:
        await self.start()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.stop()