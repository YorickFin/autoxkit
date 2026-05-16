"""High-level scrcpy-server v4.0 client facade."""

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
    """Options used to launch and connect to scrcpy-server v4.0."""

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
    """Enable ADB-over-TCP/IP before starting scrcpy-server.

    If ``tcpip_dst`` is set, the client runs ``adb connect`` to that address
    and uses it as the device serial. If ``tcpip_dst`` is not set, the client
    assumes a USB device is currently selected, reads its WLAN IP address from
    ``adb shell ip route``, runs ``adb tcpip <tcpip_port>``, then connects to
    ``<device-ip>:<tcpip_port>``.
    """

    tcpip_dst: str | None = None
    """Known wireless ADB address.

    Accepted forms are ``"192.168.1.23"`` and ``"192.168.1.23:5555"``. If the
    port is omitted, ``tcpip_port`` is appended.
    """

    tcpip_port: int = 5555
    """Wireless ADB TCP port used for ``adb tcpip`` and default address ports."""

    tcpip_disconnect_existing: bool = False
    """Run ``adb disconnect <address>`` before ``adb connect <address>``."""

    server_args: list[str] = field(default_factory=list)
    """Additional raw ``key=value`` arguments passed to ``scrcpy-server``.

    These values are appended after the arguments managed directly by
    ``ScrcpyClient``. Avoid overriding managed keys (``scid``, ``log_level``,
    ``video``, ``audio``, ``control`` and ``tunnel_forward``) unless you also
    update the Python-side connection logic accordingly.

    Common scrcpy-server v4.0 values:

    - ``video_codec``: ``h264``, ``h265`` or ``av1``.
    - ``audio_codec``: ``opus``, ``aac``, ``flac`` or ``raw``.
    - ``video_source``: ``display`` or ``camera``.
    - ``audio_source``: ``output``, ``mic``, ``playback``,
      ``mic-unprocessed``, ``mic-camcorder``, ``mic-voice-recognition``,
      ``mic-voice-communication``, ``voice-call``, ``voice-call-uplink``,
      ``voice-call-downlink`` or ``voice-performance``.
    - ``video_bit_rate`` / ``audio_bit_rate``: integer bit rate in bits/s.
    - ``max_size``: integer max video dimension, ``0`` for no limit.
    - ``max_fps``: float/integer FPS string, for example ``30`` or ``60``.
    - ``min_size_alignment``: ``1``, ``2``, ``4``, ``8`` or ``16``.
    - ``angle``: float degrees string.
    - ``crop``: ``width:height:x:y``.
    - ``video_codec_options`` / ``audio_codec_options``:
      comma-separated MediaCodec options, ``key[:type]=value``.
    - ``video_encoder`` / ``audio_encoder``: Android encoder name.
    - ``display_id``: integer display id.
    - ``new_display``: empty string, ``widthxheight``, ``/dpi`` or
      ``widthxheight/dpi``.
    - ``flex_display``: boolean.
    - ``display_ime_policy``: ``local``, ``fallback`` or ``hide``.
    - ``vd_destroy_content`` / ``vd_system_decorations``: boolean.
    - ``capture_orientation``: orientation name, optionally prefixed with
      ``@`` to lock it; ``@`` alone locks the initial orientation.
    - ``camera_id``: camera id string.
    - ``camera_size``: ``widthxheight``.
    - ``camera_facing``: ``front``, ``back`` or ``external``.
    - ``camera_ar``: ``sensor``, ``width:height`` or a float ratio.
    - ``camera_fps``: integer FPS.
    - ``camera_high_speed`` / ``camera_torch`` / ``audio_dup`` /
      ``show_touches`` / ``stay_awake`` / ``power_off_on_close`` /
      ``clipboard_autosync`` / ``downsize_on_error`` / ``cleanup`` /
      ``power_on`` / ``keep_active``: boolean.
    - ``screen_off_timeout``: integer milliseconds, or ``-1`` for unchanged.
    - ``list_encoders``, ``list_displays``, ``list_cameras``,
      ``list_camera_sizes`` and ``list_apps``: boolean listing modes.
    - ``send_device_meta``, ``send_frame_meta``, ``send_dummy_byte``,
      ``send_stream_meta`` and ``raw_stream``: protocol/testing booleans.

    Booleans are passed as ``true`` or ``false``. Values must use
    scrcpy-server v4.0 option names and wire formats; no validation or shell
    escaping is performed by this client.
    """


class ScrcpyClient:
    def __init__(self, options: ScrcpyOptions) -> None:
        if not (options.video or options.audio or options.control):
            raise ValueError("at least one of video, audio or control must be enabled")
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

        # Auto-detect TCP/IP (wireless) serials — ADB reverse does not
        # work over wireless ADB, so fall back to forward tunnel automatically.
        if self._is_tcpip_address(self.launcher.serial) and not self.options.tunnel_forward:
            print("TCP/IP device detected, using adb forward tunnel")
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
        """Return True if the serial looks like a TCP/IP address (ip:port)."""
        return serial is not None and ":" in serial

    async def _start_reverse(self) -> None:
        self._tcp_server = await asyncio.start_server(self._on_accept, self.options.host, self.options.port)
        sockets = self._tcp_server.sockets or []
        if not sockets:
            raise RuntimeError("failed to create local server socket")
        self._port = int(sockets[0].getsockname()[1])
        await self.launcher.reverse(self.socket_name, self._port)
        self._server_process = await self._start_server_process(tunnel_forward=False)
        await self._accept_streams(read_dummy_byte=False)

    async def _start_forward(self) -> None:
        self._port = self.options.port or 27183
        # Remove any stale forward mapping first to avoid conflicts
        await self.launcher.remove_forward(self._port)
        await self.launcher.forward(self.socket_name, self._port)
        self._server_process = await self._start_server_process(tunnel_forward=True)
        # Give the server time to create the LocalServerSocket before connecting
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
        raise ConnectionError(f"could not connect to forwarded scrcpy socket: {last_error}")

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
