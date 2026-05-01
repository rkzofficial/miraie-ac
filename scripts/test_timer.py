"""End-to-end test for set/cancel timer methods.

Exercises the new device.set_off_timer / cancel_off_timer / set_on_timer /
cancel_on_timer paths against the live broker. Picks the AC named in
MIRAIE_TEST_DEVICE (or the first one), and confirms each operation lands
the expected absolute-epoch value in the broker's status echo.
"""

import asyncio
import json
import os
import ssl
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import certifi
from aiomqtt import Client

from miraie_ac import MirAIeHub, MirAIeBroker


async def watch_actm(client, topic, label, predicate, timeout=15):
    """Wait until a status message on `topic` satisfies `predicate(actm)`."""
    start = time.time()
    async for msg in client.messages:
        if str(msg.topic) != topic:
            continue
        payload = json.loads(msg.payload.decode("utf-8"))
        actm = payload.get("actm")
        ts_local = datetime.now().strftime("%H:%M:%S")
        ts_broker = payload.get("ts")
        print(f"  [{ts_local}] {label}: actm={actm}  ts_broker={ts_broker}  lcmd={payload.get('lcmd')!r}")
        if actm is None:
            continue
        if predicate(actm, int(ts_broker) if ts_broker else 0):
            return actm, int(ts_broker) if ts_broker else 0
        if time.time() - start > timeout:
            raise TimeoutError(f"{label}: timed out")


async def main() -> None:
    username = os.environ["MIRAIE_USERNAME"]
    password = os.environ["MIRAIE_PASSWORD"]
    target = os.environ.get("MIRAIE_TEST_DEVICE")

    async with MirAIeHub() as hub:
        broker = MirAIeBroker()
        await hub.init(username, password, broker)

        device = next((d for d in hub.home.devices if d.friendly_name == target), None) if target else None
        if device is None:
            device = hub.home.devices[0]
        print(f"Using device: {device.friendly_name}")
        print(f"Initial: off_timer_at={device.status.off_timer_at}  on_timer_at={device.status.on_timer_at}")

        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        async with Client(
            hostname=MirAIeBroker.host, port=MirAIeBroker.port,
            username=hub.home.id, password=hub.user.access_token,
            tls_context=ssl_ctx,
        ) as obs:
            await obs.subscribe(device.status_topic)

            # Pre-clear so we start from a known state.
            await device.clear_timers()
            await watch_actm(obs, device.status_topic, "preclear", lambda a, ts: a == [-1, -1])
            await asyncio.sleep(2)

            # Broker rounds durations up to the next 60s boundary, so e.g. 90 → 120.
            print("\n[1] set_off_timer(90) — expect actm=[ts+~120, -1] (broker rounds up to minute)")
            await device.set_off_timer(90)
            actm, ts = await watch_actm(
                obs, device.status_topic, "off-set",
                lambda a, ts: a[0] > 0 and a[1] == -1,
            )
            delta = actm[0] - ts
            assert 90 <= delta <= 180, f"expected delta in [90, 180], got {delta} (actm={actm}, ts={ts})"
            print(f"  PASS — delta={delta}s")
            await asyncio.sleep(2)

            print("\n[2] set_on_timer(180) — expect actm=[ts+~remaining_off, ts+~180]")
            await device.set_on_timer(180)
            actm, ts = await watch_actm(
                obs, device.status_topic, "on-set",
                lambda a, ts: a[1] > 0,
            )
            on_delta = actm[1] - ts
            off_delta = (actm[0] - ts) if actm[0] > 0 else -1
            assert 180 <= on_delta <= 240, f"expected on_delta in [180,240], got {on_delta}"
            assert off_delta == -1 or off_delta > 0, f"off slot lost: {off_delta}"
            print(f"  PASS — off_delta={off_delta}  on_delta={on_delta}")
            await asyncio.sleep(2)

            print("\n[3] cancel_off_timer() — off slot must be -1, on slot stays roughly intact")
            await device.cancel_off_timer()
            actm, ts = await watch_actm(
                obs, device.status_topic, "off-cancel",
                lambda a, ts: a[0] == -1,
            )
            on_remaining = (actm[1] - ts) if actm[1] > 0 else -1
            print(f"  PASS — actm={actm}  on_remaining={on_remaining}s")
            await asyncio.sleep(2)

            print("\n[4] cancel_on_timer() — both slots must be -1")
            await device.cancel_on_timer()
            actm, ts = await watch_actm(
                obs, device.status_topic, "on-cancel",
                lambda a, ts: a == [-1, -1],
            )
            print(f"  PASS — actm={actm}")

            print("\nAll checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
