"""Android 设备控制模块。"""

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
    """同步 Android 设备控制器。

    将异步的 ``ScrcpyClient`` 封装在后台线程中，使所有公共方法都成为
    普通的同步调用，适合在钩子回调中使用（``key_down``、``key_up`` 等）。

    用法::

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

    # ── 连接管理 ────────────────────────────────

    def connect(
        self,
        serial: str | None = None,
        *,
        video: bool = True,
        audio: bool = True,
        control: bool = True,
        **kwargs: Any,
    ) -> None:
        """通过 scrcpy-server 连接到 Android 设备。

        参数将传递给 :class:`ScrcpyOptions`。常用额外参数：

        - ``tunnel_forward`` (bool): 使用 ``adb forward`` 而不是
          ``adb reverse``。
        - ``tcpip`` (bool): 启动前启用 ADB over TCP/IP。
        - ``tcpip_dst`` (str): 已知的无线 ADB 地址。
        """
        self._submit(
            self._connect_async(serial, video=video, audio=audio, control=control, **kwargs)
        )

    def disconnect(self) -> None:
        """断开与设备的连接并停止 scrcpy-server。"""
        self._submit(self._disconnect_async())

    @property
    def connected(self) -> bool:
        return self._client is not None

    # ── 触摸 ────────────────────────────────────────────────

    def touch(self, x: int, y: int, action: str) -> None:
        """发送触摸事件。

        Args:
            x: 屏幕 X 坐标。
            y: 屏幕 Y 坐标。
            action: ``"down"``、``"up"`` 或 ``"move"``。
        """
        action_code = {"down": 0, "up": 1, "move": 2}.get(action)
        if action_code is None:
            raise ValueError(f"无效的触摸动作：{action!r}（请使用 down/up/move）")
        self._submit(self._touch_async(action_code, x, y))

    def tap(self, x: int, y: int, delay: float = 0.05) -> None:
        """在屏幕坐标上执行点击（触摸按下然后抬起）。"""
        self.touch(x, y, "down")
        time.sleep(delay)
        self.touch(x, y, "up")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, steps: int = 10) -> None:
        """执行从 (x1, y1) 到 (x2, y2) 的滑动手势。"""
        self.touch(x1, y1, "down")
        for i in range(1, steps + 1):
            t = i / steps
            cx = int(x1 + (x2 - x1) * t)
            cy = int(y1 + (y2 - y1) * t)
            self.touch(cx, cy, "move")
        self.touch(x2, y2, "up")

    # ── 按键码 ──────────────────────────────────────────────

    def keycode(self, keycode: int, action: str = "down") -> None:
        """发送 Android 按键码事件。

        Args:
            keycode: Android 按键码（例如 4 = 返回，3 = 主页）。
            action: ``"down"`` 或 ``"up"``。
        """
        action_code = {"down": 0, "up": 1}.get(action)
        if action_code is None:
            raise ValueError(f"无效的按键动作：{action!r}（请使用 down/up）")
        self._submit(self._keycode_async(action_code, keycode))

    def key_press(self, keycode: int) -> None:
        """按下并释放按键（模拟单次点击）。"""
        self.keycode(keycode, "down")
        time.sleep(0.02)
        self.keycode(keycode, "up")

    # ── 剪贴板 ────────────────────────────────────────────

    def set_clipboard(self, text: str, paste: bool = False) -> None:
        """设置设备剪贴板（可选同时粘贴）。"""
        self._submit(self._clipboard_async(text, paste))

    # ── 内部异步辅助方法 ───────────────────────────────

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
            raise RuntimeError("未连接到设备")
        width, height = self._session_size or (1, 1)
        await self._client.control.send_touch(action, x, y, width, height)

    async def _keycode_async(self, action: int, keycode: int) -> None:
        if self._client is None or self._client.control is None:
            raise RuntimeError("未连接到设备")
        await self._client.control.send_keycode(action, keycode)

    async def _clipboard_async(self, text: str, paste: bool) -> None:
        if self._client is None or self._client.control is None:
            raise RuntimeError("未连接到设备")
        await self._client.control.set_clipboard(text, sequence=1, paste=paste)

    # ── 异步循环桥接 ─────────────────────────────────────

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
