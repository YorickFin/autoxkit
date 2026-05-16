"""Android device control module."""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from typing import Any

from .client import ScrcpyClient, ScrcpyOptions
from .adb import AdbServerLauncher
from .models import AudioVideoEvent, StreamKind

__all__ = [
    "AndroidDevice",
    "ScrcpyClient",
    "ScrcpyOptions",
    "AdbServerLauncher",
    "AudioVideoEvent",
    "StreamKind",
]


class AndroidDevice:
    """Synchronous Android device controller.

    Wraps the async ``ScrcpyClient`` in a background thread so all public
    methods are regular synchronous calls, suitable for use inside hook
    callbacks (``key_down``, ``key_up``, etc.).

    Usage::

        from autoxkit.android import AndroidDevice

        device = AndroidDevice()
        device.connect("192.168.1.23:5555")

        device.tap(500, 300)
        device.touch(500, 300, "down")
        device.keycode(4, "up")
        device.disconnect()
    """

    def __init__(
        self,
        adb_path: str | Path = Path("scrcpy-win64-v4.0") / "adb.exe",
        server_path: str | Path = Path("scrcpy-win64-v4.0") / "scrcpy-server",
    ) -> None:
        self._adb_path = Path(adb_path)
        self._server_path = Path(server_path)
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._client: ScrcpyClient | None = None
        self._session_size: tuple[int, int] | None = None

    # ── Connection management ────────────────────────────────

    def connect(
        self,
        serial: str | None = None,
        *,
        video: bool = True,
        audio: bool = True,
        control: bool = True,
        **kwargs: Any,
    ) -> None:
        """Connect to an Android device via scrcpy-server.

        Parameters are forwarded to :class:`ScrcpyOptions`.  Common extras:

        - ``tunnel_forward`` (bool): use ``adb forward`` instead of
          ``adb reverse``.
        - ``tcpip`` (bool): enable ADB-over-TCP/IP before starting.
        - ``tcpip_dst`` (str): known wireless ADB address.
        """
        self._submit(
            self._connect_async(serial, video=video, audio=audio, control=control, **kwargs)
        )

    def disconnect(self) -> None:
        """Disconnect from the device and stop the scrcpy-server."""
        self._submit(self._disconnect_async())

    @property
    def connected(self) -> bool:
        return self._client is not None

    # ── Touch ────────────────────────────────────────────────

    def touch(self, x: int, y: int, action: str) -> None:
        """Send a touch event.

        Args:
            x: Screen X coordinate.
            y: Screen Y coordinate.
            action: ``"down"``, ``"up"``, or ``"move"``.
        """
        action_code = {"down": 0, "up": 1, "move": 2}.get(action)
        if action_code is None:
            raise ValueError(f"invalid touch action: {action!r} (use down/up/move)")
        self._submit(self._touch_async(action_code, x, y))

    def tap(self, x: int, y: int, delay: float = 0.05) -> None:
        """Perform a tap (touch down then up) at screen coordinates."""
        self.touch(x, y, "down")
        time.sleep(delay)
        self.touch(x, y, "up")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, steps: int = 10) -> None:
        """Perform a swipe gesture from (x1, y1) to (x2, y2)."""
        self.touch(x1, y1, "down")
        for i in range(1, steps + 1):
            t = i / steps
            cx = int(x1 + (x2 - x1) * t)
            cy = int(y1 + (y2 - y1) * t)
            self.touch(cx, cy, "move")
        self.touch(x2, y2, "up")

    # ── Keycode ──────────────────────────────────────────────

    def keycode(self, keycode: int, action: str = "down") -> None:
        """Send an Android keycode event.

        Args:
            keycode: Android keycode (e.g. 4 = BACK, 3 = HOME).
            action: ``"down"`` or ``"up"``.
        """
        action_code = {"down": 0, "up": 1}.get(action)
        if action_code is None:
            raise ValueError(f"invalid key action: {action!r} (use down/up)")
        self._submit(self._keycode_async(action_code, keycode))

    def key_press(self, keycode: int) -> None:
        """Press and release a key (simulates a single tap)."""
        self.keycode(keycode, "down")
        time.sleep(0.02)
        self.keycode(keycode, "up")

    # ── Clipboard ────────────────────────────────────────────

    def set_clipboard(self, text: str, paste: bool = False) -> None:
        """Set the device clipboard (optionally also paste)."""
        self._submit(self._clipboard_async(text, paste))

    # ── Internal async helpers ───────────────────────────────

    async def _connect_async(
        self,
        serial: str | None,
        video: bool,
        audio: bool,
        control: bool,
        **kwargs: Any,
    ) -> None:
        if self._client is not None:
            return
        opts = ScrcpyOptions(
            serial=serial,
            adb_path=self._adb_path,
            server_path=self._server_path,
            video=video,
            audio=audio,
            control=control,
            **kwargs,
        )
        client = ScrcpyClient(opts)
        await client.start()
        self._client = client

    async def _disconnect_async(self) -> None:
        if self._client is None:
            return
        await self._client.stop()
        self._client = None
        self._session_size = None

    async def _touch_async(self, action: int, x: int, y: int) -> None:
        if self._client is None or self._client.control is None:
            raise RuntimeError("device not connected")
        width, height = self._session_size or (1, 1)
        await self._client.control.send_touch(action, x, y, width, height)

    async def _keycode_async(self, action: int, keycode: int) -> None:
        if self._client is None or self._client.control is None:
            raise RuntimeError("device not connected")
        await self._client.control.send_keycode(action, keycode)

    async def _clipboard_async(self, text: str, paste: bool) -> None:
        if self._client is None or self._client.control is None:
            raise RuntimeError("device not connected")
        await self._client.control.set_clipboard(text, sequence=1, paste=paste)

    # ── Async loop bridge ────────────────────────────────────

    def _submit(self, coro: Any) -> Any:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def __enter__(self) -> AndroidDevice:
        return self

    def __exit__(self, *args: Any) -> None:
        self.disconnect()
