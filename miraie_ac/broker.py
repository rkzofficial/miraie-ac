from aiomqtt import Client, Message, MqttError
import asyncio
import ssl
import certifi
import random
import json
from .enums import PowerMode, HVACMode, FanMode, PresetMode, SwingMode, DisplayMode, ConvertiMode
from .user import User
from .logger import LOGGER


class MirAIeBroker:
    host = "mqtt.miraie.in"
    port = 8883
    use_ssl = True
    client_id = f"ha-mirae-mqtt-{random.randint(0, 1000)}"
    reconnect_interval = 5  # In seconds

    def __init__(self) -> None:
        self.status_callbacks: dict[str, callable] = {}

    def register_device_callback(self, topic: str, callback):
        self.status_callbacks[topic] = callback

    def remove_device_callback(self, topic: str):
        self.status_callbacks.pop(topic, None)

    def set_topics(self, topics: list[str]):
        self.commandTopics = topics

    async def on_connect(self):
        for topic in self.commandTopics:
            print("Subscribing to topic: ", topic)
            await self.client.subscribe(topic)

    def on_message(self, message: Message):
        parsed = json.loads(message.payload.decode("utf-8"))
        func = self.status_callbacks.get(message.topic.value)
        func(parsed)

    async def connect(self, username: str, access_token: User, get_token):
        # Set on_token_expire callback
        password = access_token

        context = None

        if self.use_ssl:
            context = ssl.create_default_context(cafile=certifi.where())

        while True:
            try:
                async with Client(
                    hostname=self.host,
                    port=self.port,
                    username=username,
                    password=password,
                    tls_context=context,
                ) as client:
                    self.client = client
                    await self.on_connect()
                    LOGGER.info(f"Broker connection has been established")
                    async for message in client.messages:
                        self.on_message(message)

            except MqttError as error:
                LOGGER.error(f'Error "{error}". Reconnecting in {self.reconnect_interval} seconds.')
                password = await get_token()
                await asyncio.sleep(self.reconnect_interval)

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

    async def set_power(self, topic: str, power: PowerMode):
        await self.client.publish(topic, json.dumps(self.build_power_payload(power)))

    # Temperature
    def build_temperature_payload(self, temperature: float):
        payload = self.build_base_payload()
        payload["actmp"] = str(temperature)
        return payload

    async def set_temperature(self, topic: str, temperature: float):
        await self.client.publish(
            topic, json.dumps(self.build_temperature_payload(temperature))
        )

    # HVAC Mode
    def build_hvac_mode_payload(self, mode: HVACMode):
        payload = self.build_base_payload()
        payload["acmd"] = str(mode.value)
        return payload

    async def set_hvac_mode(self, topic: str, mode: HVACMode):
        await self.client.publish(topic, json.dumps(self.build_hvac_mode_payload(mode)))

    # Fan Mode
    def build_fan_mode_payload(self, mode: FanMode):
        payload = self.build_base_payload()
        payload["acfs"] = str(mode.value)
        return payload

    async def set_fan_mode(self, topic: str, mode: FanMode):
        await self.client.publish(topic, json.dumps(self.build_fan_mode_payload(mode)))

    # Preset Mode
    def build_preset_mode_payload(self, mode: PresetMode):
        payload = self.build_base_payload()

        if mode == PresetMode.NONE:
            payload["acem"] = "off"
            payload["acpm"] = "off"
            payload["acec"] = "off"
            payload["cnv"] = 0
        elif mode == PresetMode.ECO:
            payload["acem"] = "on"
            payload["acpm"] = "off"
            payload["acec"] = "off"
            payload["actmp"] = 26.0
            payload["cnv"] = 0
        elif mode == PresetMode.BOOST:
            payload["acem"] = "off"
            payload["acpm"] = "on"
            payload["acec"] = "off"
            payload["cnv"] = 0
        elif mode == PresetMode.CLEAN:
            payload["acem"] = "off"
            payload["acpm"] = "off"
            payload["acec"] = "on"
            payload["cnv"] = 0
        return payload

    async def set_preset_mode(self, topic: str, mode: PresetMode):
        await self.client.publish(
            topic, json.dumps(self.build_preset_mode_payload(mode))
        )

    # Vertical Swing Mode
    def build_v_swing_mode_payload(self, mode: SwingMode):
        payload = self.build_base_payload()
        payload["acvs"] = mode.value
        return payload

    async def set_v_swing_mode(self, topic: str, mode: SwingMode):
        await self.client.publish(
            topic, json.dumps(self.build_v_swing_mode_payload(mode))
        )
    
    # Horizontal Swing Mode
    def build_h_swing_mode_payload(self, mode: SwingMode):
        payload = self.build_base_payload()
        payload["achs"] = mode.value
        return payload

    async def set_h_swing_mode(self, topic: str, mode: SwingMode):
        await self.client.publish(
            topic, json.dumps(self.build_h_swing_mode_payload(mode))
        )

    # Display Mode
    def build_display_mode_payload(self, mode: DisplayMode):
        payload = self.build_base_payload()
        payload["acdc"] = str(mode.value)
        return payload

    async def set_display_mode(self, topic: str, mode: DisplayMode):
        await self.client.publish(
            topic, json.dumps(self.build_display_mode_payload(mode))
        )
        
    # Converti Mode
    def build_converti_mode_payload(self, mode: ConvertiMode):
        payload = self.build_base_payload()
        payload["acem"] = "off"
        payload["acpm"] = "off"
        payload["cnv"] = mode.value
        return payload

    async def set_converti_mode(self, topic: str, mode: ConvertiMode):
        await self.client.publish(
            topic, json.dumps(self.build_converti_mode_payload(mode))
        )
