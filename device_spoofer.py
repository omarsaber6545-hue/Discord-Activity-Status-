import os
import sys
import json
import time
import asyncio
import threading
import logging
from typing import Optional, Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Device Platform Configurations with exact VR & Console Gateway signatures
PLATFORM_PRESETS = {
    "vr_oculus": {
        "title": "🥽 VR Headset Icon (Discord Oculus Signature)",
        "os": "Android",
        "browser": "Discord Oculus",
        "device": "Oculus Quest",
        "activity_name": "Virtual Reality VR 🥽",
        "activity_details": "Exploring Virtual Reality 🥽",
        "activity_state": "Oculus Quest 3 Active",
        "platform_key": "vr"
    },
    "vr_discord_vr": {
        "title": "🥽 VR Headset Icon (Discord VR Signature)",
        "os": "Oculus",
        "browser": "Discord VR",
        "device": "Quest 3",
        "activity_name": "Oculus Quest 3 VR 🥽",
        "activity_details": "Exploring Virtual Reality 🥽",
        "activity_state": "Meta Quest 3 Active",
        "platform_key": "vr"
    },
    "vr_desktop": {
        "title": "🥽 VR Headset (Desktop 🖥️ Icon)",
        "os": "Windows",
        "browser": "Discord Client",
        "device": "",
        "activity_name": "Oculus Quest 3 VR 🥽",
        "activity_details": "Exploring Virtual Reality 🥽",
        "activity_state": "Meta Quest 3 Active",
        "platform_key": "vr"
    },
    "vr_mobile": {
        "title": "🥽 VR Headset (Mobile 📱 Icon)",
        "os": "Android",
        "browser": "Discord Android",
        "device": "Oculus Quest 3",
        "activity_name": "Oculus Quest 3 VR 🥽",
        "activity_details": "Exploring Virtual Reality 🥽",
        "activity_state": "Meta Quest 3 Active",
        "platform_key": "vr"
    },
    "ps5_desktop": {
        "title": "🎮 PlayStation 5 (Desktop 🖥️ Icon)",
        "os": "Windows",
        "browser": "Discord Client",
        "device": "",
        "activity_name": "PlayStation 5 🎮",
        "activity_details": "Playing on PlayStation 5",
        "activity_state": "PlayStation Network Active",
        "platform_key": "ps5"
    },
    "ps5_mobile": {
        "title": "🎮 PlayStation 5 (Mobile 📱 Icon)",
        "os": "Android",
        "browser": "Discord Android",
        "device": "PlayStation 5",
        "activity_name": "PlayStation 5 🎮",
        "activity_details": "Playing on PlayStation 5",
        "activity_state": "PlayStation Network Active",
        "platform_key": "ps5"
    },
    "mobile": {
        "title": "📱 Mobile Phone (iPhone / Android 📱 Icon)",
        "os": "Android",
        "browser": "Discord Android",
        "device": "Samsung Galaxy S24",
        "activity_name": "Discord for Mobile 📱",
        "activity_details": "Mobile Active",
        "activity_state": "Mobile Online",
        "platform_key": "mobile"
    }
}


class DeviceSpooferWorker:
    """Manages Gateway WebSocket session to spoof VR / PlayStation / Mobile device status icons."""

    def __init__(self):
        self.is_running = False
        self.is_connected = False
        self.token = ""
        self.platform_mode = "vr_oculus"
        self.custom_details = ""
        self.status_type = "online"
        self.status_message = "🔴 Device Spoofer Stopped"
        self.user_tag = ""
        self.user_id = ""
        self.start_time = time.time()
        self.stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None

    def start(
        self,
        token: str,
        platform_mode: str = "vr_oculus",
        custom_details: str = "",
        status_type: str = "online"
    ) -> Tuple[bool, str]:
        """Starts Device Platform Spoofer in background thread."""
        if self.is_running:
            return False, "Device spoofer is already running!"

        self.token = token.strip()
        self.platform_mode = platform_mode.lower().strip()
        if self.platform_mode not in PLATFORM_PRESETS:
            self.platform_mode = "vr_oculus"

        self.custom_details = custom_details.strip()
        self.status_type = status_type.strip() if status_type.strip() in ("online", "idle", "dnd") else "online"

        if not self.token:
            return False, "Please enter your Token first!"

        self.stop_event.clear()
        self.is_running = True
        self.start_time = time.time()
        preset_info = PLATFORM_PRESETS[self.platform_mode]
        self.status_message = f"🔄 Activating {preset_info['title']}..."

        self.worker_thread = threading.Thread(target=self._run_spoofer_loop, daemon=True)
        self.worker_thread.start()
        return True, f"🚀 Activating Status Icon: {preset_info['title']}"

    def _run_spoofer_loop(self):
        """Asyncio loop running Gateway WebSocket session with spoofed device properties."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._spoofer_gateway_session())
        except Exception as e:
            logging.error(f"Device spoofer error: {e}")
            self.status_message = f"❌ Spoofer Error: {e}"
        finally:
            self.is_running = False
            self.is_connected = False

    async def _spoofer_gateway_session(self):
        """Gateway WebSocket session with spoofed device properties & activity platform."""
        import websockets

        auth_header = self.token if not self.token.startswith("Bot ") else self.token
        gateway_url = "wss://gateway.discord.gg/?v=9&encoding=json"
        preset = PLATFORM_PRESETS.get(self.platform_mode, PLATFORM_PRESETS["vr_oculus"])

        details_txt = self.custom_details if self.custom_details else preset["activity_details"]
        start_ms = int(self.start_time * 1000)

        while self.is_running and not self.stop_event.is_set():
            try:
                # Set max_size=None to handle large READY payloads (> 1MB)
                async with websockets.connect(gateway_url, max_size=None) as ws:
                    hello_raw = await ws.recv()
                    hello = json.loads(hello_raw)
                    heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000.0

                    activity_obj = {
                        "name": preset["activity_name"],
                        "type": 0,
                        "details": details_txt,
                        "state": preset["activity_state"],
                        "platform": preset["platform_key"],
                        "timestamps": {
                            "start": start_ms
                        }
                    }

                    identify_payload = {
                        "op": 2,
                        "d": {
                            "token": auth_header,
                            "capabilities": 125,
                            "properties": {
                                "os": preset["os"],
                                "browser": preset["browser"],
                                "device": preset["device"]
                            },
                            "presence": {
                                "status": self.status_type,
                                "since": start_ms,
                                "activities": [activity_obj],
                                "afk": False
                            }
                        }
                    }
                    await ws.send(json.dumps(identify_payload))

                    last_heartbeat = time.time()

                    while self.is_running and not self.stop_event.is_set():
                        now = time.time()
                        if now - last_heartbeat >= heartbeat_interval:
                            await ws.send(json.dumps({"op": 1, "d": None}))
                            last_heartbeat = now

                        try:
                            msg_raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            packet = json.loads(msg_raw)

                            op = packet.get("op")
                            event_type = packet.get("t")
                            data = packet.get("d", {})

                            if op == 0 and event_type == "READY":
                                user_obj = data.get("user", {})
                                self.user_id = str(user_obj.get("id", ""))
                                username = user_obj.get("username", "Account")
                                self.user_tag = username
                                self.is_connected = True
                                self.status_message = f"🟢 Device Status Icon Active: {preset['title']} ({self.user_tag})"
                                logging.info(f"Device Spoofer READY: {preset['title']} for {self.user_tag}")

                            elif op == 1:
                                await ws.send(json.dumps({"op": 1, "d": None}))

                        except asyncio.TimeoutError:
                            pass

            except Exception as e:
                logging.warning(f"Device spoofer reconnect pulse: {e}. Reconnecting in 3s...")
                self.is_connected = False
                self.status_message = f"🔄 Reconnecting {preset['title']}..."
                await asyncio.sleep(3)

    def stop(self):
        """Stops Device Spoofer."""
        self.stop_event.set()
        self.is_running = False
        self.is_connected = False
        self.status_message = "🔴 Device Spoofer Stopped."
