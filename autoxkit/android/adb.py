"""ADB launcher for scrcpy-server v4.0."""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

if os.name == "nt":
    _CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
else:
    _CREATE_NO_WINDOW = 0


class AdbError(RuntimeError):
    pass


@dataclass(slots=True)
class AdbServerLauncher:
    adb_path: Path
    server_path: Path
    serial: str | None = None
    device_server_path: str = "/data/local/tmp/scrcpy-server.jar"

    async def connect_tcpip(self, address: str) -> None:
        stdout, stderr = await self._adb_global_output("connect", address)
        message = f"{stdout}\n{stderr}".lower()
        if "failed" in message or "unable" in message or "cannot" in message:
            raise AdbError((stderr or stdout).strip())
        self.serial = address

    async def disconnect_tcpip(self, address: str) -> None:
        await self._adb_global("disconnect", address, check=False)

    async def enable_tcpip(self, port: int = 5555) -> None:
        await self._adb("tcpip", str(port))

    async def get_device_ip(self) -> str:
        """Parse the Wi-Fi IP address from `adb shell ip route`.

        Only considers lines where the interface name starts with ``wlan``,
        matching the official scrcpy behavior to skip non-Wi-Fi interfaces
        such as rmnet_data (mobile data) or usb0 (USB tethering).
        """
        route = await self.shell_output("ip", "route")
        for line in route.splitlines():
            # Look for lines like:
            #   192.168.1.0/24 dev wlan0  proto kernel  scope link  src 192.168.1.x
            fields = line.split()
            for i, field in enumerate(fields):
                if field == "dev" and i + 1 < len(fields) and fields[i + 1].startswith("wlan"):
                    # Found a wlan line, extract the src IP
                    for j, f in enumerate(fields):
                        if f == "src" and j + 1 < len(fields):
                            ip = fields[j + 1]
                            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                                return ip
        raise AdbError(
            f"could not find Wi-Fi (wlan) device ip in `adb shell ip route`: {route.strip()}"
        )

    async def discover_usb_serial(self) -> str | None:
        """Discover the serial of a single USB-connected device.

        Returns None if there is no USB device, or if there are multiple.
        """
        proc = await asyncio.create_subprocess_exec(
            str(self.adb_path),
            "devices", "-l",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=_CREATE_NO_WINDOW,
        )
        stdout, _ = await proc.communicate()
        out = stdout.decode(errors="replace")

        usb_serials = []
        for line in out.splitlines():
            # Skip empty lines and the "List of devices attached" header
            if not line.strip() or not line[0].isalnum():
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial = parts[0]
            state = parts[1]
            if state != "device":
                continue
            # USB devices have serials without ":"
            # TCP/IP devices have format ip:port
            if ":" not in serial:
                usb_serials.append(serial)

        if len(usb_serials) == 1:
            return usb_serials[0]
        return None

    async def shell_output(self, *args: str) -> str:
        stdout, _ = await self._adb_output("shell", *args)
        return stdout

    async def push_server(self) -> None:
        await self._adb("push", str(self.server_path), self.device_server_path)

    async def reverse(self, socket_name: str, port: int) -> None:
        await self._adb("reverse", f"localabstract:{socket_name}", f"tcp:{port}")

    async def remove_reverse(self, socket_name: str) -> None:
        await self._adb("reverse", "--remove", f"localabstract:{socket_name}", check=False)

    async def forward(self, socket_name: str, port: int) -> None:
        await self._adb("forward", f"tcp:{port}", f"localabstract:{socket_name}")

    async def remove_forward(self, port: int) -> None:
        await self._adb("forward", "--remove", f"tcp:{port}", check=False)

    async def start_server_process(
        self,
        *,
        version: str,
        scid: int,
        tunnel_forward: bool,
        video: bool,
        audio: bool,
        control: bool,
        log_level: str,
        extra_args: list[str] | None = None,
    ) -> asyncio.subprocess.Process:
        args = [
            str(self.adb_path),
            *self._serial_args(),
            "shell",
            f"CLASSPATH={self.device_server_path}",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            version,
            f"scid={scid:08x}",
            f"log_level={log_level}",
        ]
        if tunnel_forward:
            args.append("tunnel_forward=true")
        if not video:
            args.append("video=false")
        if not audio:
            args.append("audio=false")
        if not control:
            args.append("control=false")
        if extra_args:
            args.extend(extra_args)

        return await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=_CREATE_NO_WINDOW,
        )

    async def _adb(self, *args: str, check: bool = True) -> asyncio.subprocess.Process:
        proc, _, _ = await self._run_adb([*self._serial_args(), *args], check=check)
        return proc

    async def _adb_global(self, *args: str, check: bool = True) -> asyncio.subprocess.Process:
        proc, _, _ = await self._run_adb([*args], check=check)
        return proc

    async def _adb_output(self, *args: str, check: bool = True) -> tuple[str, str]:
        _, stdout, stderr = await self._run_adb([*self._serial_args(), *args], check=check)
        return stdout, stderr

    async def _adb_global_output(self, *args: str, check: bool = True) -> tuple[str, str]:
        _, stdout, stderr = await self._run_adb([*args], check=check)
        return stdout, stderr

    async def _run_adb(self, args: list[str], check: bool = True) -> tuple[asyncio.subprocess.Process, str, str]:
        proc = await asyncio.create_subprocess_exec(
            str(self.adb_path),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=_CREATE_NO_WINDOW,
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode(errors="replace").strip()
        err = stderr.decode(errors="replace").strip()
        if check and proc.returncode:
            raise AdbError(f"adb {' '.join(args)} failed: {err or out}")
        return proc, out, err

    def _serial_args(self) -> list[str]:
        return ["-s", self.serial] if self.serial else []
