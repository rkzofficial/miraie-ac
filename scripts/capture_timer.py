"""Probe script for reverse-engineering the MirAIe timer payload.

Reads MIRAIE_USERNAME and MIRAIE_PASSWORD from the environment, logs in,
subscribes to every AC's status topic, and prints the full JSON payload
every time it changes — with the `actm` field highlighted.

Usage:
  export MIRAIE_USERNAME=...
  export MIRAIE_PASSWORD=...
  python scripts/capture_timer.py

Then on your phone, open the MirAIe app and:
  1. Set an "OFF timer" for 1 hour. Watch the output. Note `actm`.
  2. Set "OFF timer" for 2 hours. Note `actm`.
  3. Cancel OFF timer. Note `actm`.
  4. Repeat for ON timer at 30 min, 4 hours, etc.

The goal is to determine: position (which slot is on vs off), unit
(minutes / hours / epoch), and how cancellation is encoded.
"""

import asyncio
import json
import os
import ssl
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import certifi
from aiomqtt import Client

from miraie_ac import MirAIeHub, MirAIeBroker


def hl(payload: dict) -> str:
    actm = payload.get("actm")
    return f"actm={actm!r}  full={json.dumps(payload, sort_keys=True)}"


async def main() -> None:
    username = os.environ["MIRAIE_USERNAME"]
    password = os.environ["MIRAIE_PASSWORD"]

    async with MirAIeHub() as hub:
        broker = MirAIeBroker()
        await hub.init(username, password, broker)

        print(f"Logged in. Home: {hub.home.id}")
        print("Devices:")
        topics: list[str] = []
        for d in hub.home.devices:
            print(f"  - {d.friendly_name}  status={d.status_topic}")
            topics.append(d.status_topic)

        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        async with Client(
            hostname=MirAIeBroker.host,
            port=MirAIeBroker.port,
            username=hub.home.id,
            password=hub.user.access_token,
            tls_context=ssl_ctx,
        ) as client:
            for t in topics:
                await client.subscribe(t)
            print(f"\nSubscribed to {len(topics)} status topics. Waiting for updates...\n")
            print("Set timers in the MirAIe phone app and watch this output.\n")

            device_by_topic = {d.status_topic: d.friendly_name for d in hub.home.devices}
            async for msg in client.messages:
                ts = datetime.now().strftime("%H:%M:%S")
                topic = str(msg.topic)
                name = device_by_topic.get(topic, topic)
                try:
                    payload = json.loads(msg.payload.decode("utf-8"))
                    print(f"EVENT {ts} dev={name!r} {hl(payload)}")
                except Exception as e:
                    print(f"EVENT {ts} dev={name!r} parse_error={e} raw={msg.payload!r}")


if __name__ == "__main__":
    asyncio.run(main())
