from paho.mqtt import client as mqtt
import ssl
import certifi
import random
import json
from .enums import *


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

    def on_connect(self, client: mqtt.Client, userdata, flags, rc):
        # Subscribe to all command topics
        for topic in self.commandTopics:
            client.subscribe(topic)

    def on_message(self, client: mqtt.Client, userdata, msg):
        parsed = json.loads(msg.payload.decode("utf-8"))

        func = self.status_callbacks.get(msg.topic)
        func(parsed)

    def on_disconnect(self, client: mqtt.Client, userdata, rc):
        if rc != 0:
            client.reconnect()

    def on_log(self, client, userdata, level, buf):
        print("log: ", buf)

    def connect(self, username: str, password: str):
        # Create MQTT client
        client = mqtt.Client(
            self.client_id,
            True,
        )

        # Set username and password
        client.username_pw_set(username, password)

        if self.use_ssl:
            # Create ssl context with TLSv1
            context = ssl.create_default_context(cafile=certifi.where())
            client.tls_set_context(context)
            client.tls_insecure_set(True)

        # Set callbacks
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect
        # client.on_log = self.on_log

        # Connect to MQTT broker
        client.connect(self.host, self.port, 60)

        # Start network loop
        self.client = client
        self.client.loop_start()

    def build_base_payload(self):
        return {
            "ki": 1,
            "cnt": "an",
            "sid": "1",
        }

    # Power
    def build_power_payload(self, power: PowerMode):
        payload = self.build_base_payload()
        payload["ps"] = str(power)
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
        payload["acmd"] = str(mode)
        return payload

    def set_hvac_mode(self, topic: str, mode: HVACMode):
        self.client.publish(topic, json.dumps(self.build_hvac_mode_payload(mode)))

    # Fan Mode
    def build_fan_mode_payload(self, mode: FanMode):
        payload = self.build_base_payload()
        payload["acfs"] = str(mode)
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
        payload["acvs"] = str(mode)
        return payload

    def set_swing_mode(self, topic: str, mode: SwingMode):
        self.client.publish(topic, json.dumps(self.build_swing_mode_payload(mode)))
