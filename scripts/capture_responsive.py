"""Capture local responsive smoke-test screenshots with Chrome's DevTools protocol."""
import base64
import json
import os
import re
import socket
import struct
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9223


class DevTools:
    def __init__(self, url):
        host = "127.0.0.1"
        path = url.split(f"ws://{host}:{PORT}", 1)[1]
        self.socket = socket.create_connection((host, PORT), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {path} HTTP/1.1\r\nHost: {host}:{PORT}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode())
        response = self.socket.recv(4096)
        if b" 101 " not in response:
            raise RuntimeError(response.decode(errors="replace"))
        self.command_id = 0

    def _send(self, payload):
        data = json.dumps(payload).encode()
        mask = os.urandom(4)
        length = len(data)
        header = bytearray([0x81])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        self.socket.sendall(bytes(header) + mask + masked)

    def _receive(self):
        first = self.socket.recv(2)
        if len(first) < 2:
            raise RuntimeError("Chrome closed the DevTools connection")
        length = first[1] & 0x7F
        if length == 126:
            length = struct.unpack("!H", self.socket.recv(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self.socket.recv(8))[0]
        chunks = bytearray()
        while len(chunks) < length:
            chunks.extend(self.socket.recv(length - len(chunks)))
        return json.loads(chunks.decode())

    def command(self, method, params=None):
        self.command_id += 1
        current = self.command_id
        self._send({"id": current, "method": method, "params": params or {}})
        while True:
            message = self._receive()
            if message.get("id") == current:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})


def wait_for_target():
    for _ in range(50):
        try:
            targets = json.load(urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=1))
            if targets:
                return targets[0]["webSocketDebuggerUrl"]
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("Chrome DevTools did not start")


def main():
    chrome = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            f"--remote-debugging-port={PORT}",
            "--user-data-dir=/tmp/cereqo-cdp-profile",
            "--no-first-run",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        tools = DevTools(wait_for_target())
        tasks_html = urlopen("http://127.0.0.1:8000/tasks/", timeout=3).read().decode()
        homework_match = re.search(r'href="/tasks/(\d+)/"', tasks_html)
        homework_path = f"/tasks/{homework_match.group(1)}/" if homework_match else "/tasks/"
        matrix = [
            ("home-uz-light", 390, 900, "/", "uz", "light"),
            ("home-en-dark", 1440, 900, "/", "en", "dark"),
            ("learn-uz-dark", 390, 900, "/learn/", "uz", "dark"),
            ("tasks-en-light", 375, 900, "/tasks/", "en", "light"),
            ("homework-uz-light", 390, 900, homework_path, "uz", "light"),
            ("attendance-uz-dark", 768, 900, "/attendance/", "uz", "dark"),
            ("rank-en-light", 375, 900, "/leaderboard/", "en", "light"),
        ]
        for label, width, height, path, language, theme in matrix:
            tools.command(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": width < 768},
            )
            tools.command("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": theme}]})
            tools.command("Network.setCookie", {"name": "django_language", "value": language, "domain": "127.0.0.1", "path": "/"})
            tools.command("Page.navigate", {"url": f"http://127.0.0.1:8000{path}"})
            time.sleep(0.7)
            tools.command("Runtime.evaluate", {"expression": "window.scrollTo(0, 0)"})
            state = tools.command("Runtime.evaluate", {"expression": "document.documentElement.dataset.theme + ':' + document.documentElement.lang", "returnByValue": True})
            result = tools.command("Page.captureScreenshot", {"format": "png", "fromSurface": True})
            output = Path(f"/tmp/cereqo-cdp-{label}-{width}.png")
            output.write_bytes(base64.b64decode(result["data"]))
            print(output, state.get("result", {}).get("value"))
    finally:
        chrome.terminate()
        chrome.wait(timeout=5)


if __name__ == "__main__":
    main()
