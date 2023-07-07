from asyncio_paho import AsyncioPahoClient as MQTTClient
import asyncio
import ssl
import certifi
import random
import json
from .enums import *
from .user import User


class MirAIeBroker:
    host = "mqtt.miraie.in"
    port = 8883
    use_ssl = True
    client_id = f"ha-mirae-mqtt-{random.randint(0, 1000)}"

    def __init__(self) -> None:
        self.status_callbacks: dict[str, list[callable]] = {}

    def register_device_callback(self, topic: str, callback):
        self.status_callbacks[topic] = callback

    def remove_device_callback(self, topic: str):
        self.status_callbacks.pop(topic, None)

    def set_topics(self, topics: list[str]):
        self.commandTopics = topics

    async def on_connect(self, client: MQTTClient, userdata, flags, rc):
        # Subscribe to all command topics
        for topic in self.commandTopics:
            print("Subscribing to topic: ", topic)
            await client.asyncio_subscribe(topic)

    async def on_message(self, client: MQTTClient, userdata, msg):
        print("Received message: ", msg.topic, msg.payload)
        parsed = json.loads(msg.payload.decode("utf-8"))

        func = self.status_callbacks.get(msg.topic)
        func(parsed)

    def on_disconnect(self, client: MQTTClient, userdata, rc):
        def cb(username: str, access_token: User):
            self.client.username_pw_set(username, access_token)
            self.client.reconnect()

        if rc != 0:
            asyncio.create_task(self.on_get_token(cb))

    def on_log(self, client, userdata, level, buf):
        print("log: ", buf)

    async def connect(self, username: str, access_token: User, on_get_token):
        # Set on_token_expire callback
        self.on_get_token = on_get_token

        # Create MQTT client
        async with MQTTClient(self.client_id, True) as client:
            # Set username and password
            client.username_pw_set(username, access_token)

            if self.use_ssl:
                # Create ssl context with TLSv1
                context = ssl.create_default_context(cafile=certifi.where())
                client.tls_set_context(context)
                client.tls_insecure_set(True)

            # Set callbacks
            client.asyncio_listeners.add_on_connect(self.on_connect)
            client.asyncio_listeners.add_on_message(self.on_message)

            await client.asyncio_connect(self.host, self.port, 60)

            print("Connected to MQTT broker")

    def build_base_payload(self):
        return {
            "ki": 1,
            "cnt": "an",
            "sid": "1",
        }

    # Power
    def build_power_payload(self, power: PowerMode):
        payload = self.build_base_payload()
        payload["ps"] = str(power.value)
        return payload

    def set_power(self, topic: str, power: PowerMode):
        self.client.publish(topic, json.dumps(self.build_power_payload(power)))

    # Temperature
    def build_temperature_payload(self, temperature: float):
        payload = self.build_base_payload()
        payload["actmp"] = str(temperature)
        return payload

    def set_temperature(self, topic: str, temperature: float):
        self.client.publish(
            topic, json.dumps(self.build_temperature_payload(temperature))
        )

    # HVAC Mode
    def build_hvac_mode_payload(self, mode: HVACMode):
        payload = self.build_base_payload()
        payload["acmd"] = str(mode.value)
        return payload

    def set_hvac_mode(self, topic: str, mode: HVACMode):
        self.client.publish(topic, json.dumps(self.build_hvac_mode_payload(mode)))

    # Fan Mode
    def build_fan_mode_payload(self, mode: FanMode):
        payload = self.build_base_payload()
        payload["acfs"] = str(mode.value)
        return payload

    def set_fan_mode(self, topic: str, mode: FanMode):
        self.client.publish(topic, json.dumps(self.build_fan_mode_payload(mode)))

    # Preset Mode
    def build_preset_mode_payload(self, mode: PresetMode):
        payload = self.build_base_payload()

        if mode == PresetMode.NONE:
            payload["acem"] = "off"
            payload["acpm"] = "off"
        elif mode == PresetMode.ECO:
            payload["acem"] = "on"
            payload["acpm"] = "off"
            payload["actmp"] = 26.0
        elif mode == PresetMode.BOOST:
            payload["acem"] = "off"
            payload["acpm"] = "on"
        return payload

    def set_preset_mode(self, topic: str, mode: PresetMode):
        self.client.publish(topic, json.dumps(self.build_preset_mode_payload(mode)))

    # Swing Mode
    def build_swing_mode_payload(self, mode: SwingMode):
        payload = self.build_base_payload()
        payload["acvs"] = mode.value
        return payload

    def set_swing_mode(self, topic: str, mode: SwingMode):
        self.client.publish(topic, json.dumps(self.build_swing_mode_payload(mode)))
