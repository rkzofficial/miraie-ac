from typing import Callable
from .broker import MirAIeBroker
from .enums import *


class DeviceStatus:
    def __init__(
        self,
        is_online: bool,
        temperature: float,
        room_temperature: float,
        power_mode: PowerMode,
        fan_mode: FanMode,
        swing_mode: SwingMode,
        display_mode: DisplayMode,
        hvac_mode: HVACMode,
        preset_mode: PresetMode,
    ):
        self.is_online = is_online
        self.temperature = temperature
        self.room_temperature = room_temperature
        self.power_mode = power_mode
        self.fan_mode = fan_mode
        self.swing_mode = swing_mode
        self.display_mode = display_mode
        self.hvac_mode = hvac_mode
        self.preset_mode = preset_mode


class DeviceDetails:
    def __init__(
        self,
        model_name,
        mac_address,
        category,
        brand,
        firmware_version,
        serial_number,
        model_number,
        product_serial_number,
    ):
        self.model_name = model_name
        self.mac_address = mac_address
        self.category = category
        self.brand = brand
        self.firmware_version = firmware_version
        self.serial_number = serial_number
        self.model_number = model_number
        self.product_serial_number = product_serial_number


class Device:
    def __init__(
        self,
        id: str,
        name: str,
        friendly_name: str,
        control_topic: str,
        status_topic: str,
        connection_status_topic: str,
        broker: MirAIeBroker,
    ):
        self.id = id
        self.name = name
        self.friendly_name = friendly_name
        self.control_topic = control_topic
        self.status_topic = status_topic
        self.connection_status_topic = connection_status_topic
        self.broker = broker

        self._callbacks = set()
        self.broker.register_device_callback(self.status_topic, self.status_handler)
        self.broker.register_device_callback(
            self.connection_status_topic, self.connection_status_handler
        )

    def __del__(self):
        self.broker.remove_device_callback(self.status_topic)
        self.broker.remove_device_callback(self.connection_status_topic)

    def refresh(self):
        for callback in self._callbacks:
            callback()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    def status_handler(self, status: any):
        status_obj = DeviceStatus(
            is_online=self.status.is_online,
            temperature=float(status["actmp"]),
            room_temperature=float(status["rmtmp"]),
            power_mode=PowerMode(status["ps"]),
            fan_mode=FanMode(status["acfs"]),
            swing_mode=SwingMode(status["acvs"]),
            display_mode=DisplayMode(status["acdc"]),
            hvac_mode=HVACMode(status["acmd"]),
            preset_mode=PresetMode.BOOST
            if status["acpm"] == "on"
            else PresetMode.ECO
            if status["acem"] == "on"
            else PresetMode.NONE,
        )

        self.set_status(status_obj)
        self.refresh()

    def connection_status_handler(self, status: any):
        self.status.is_online = status["onlineStatus"] == "true"
        self.refresh()

    def set_details(self, details: DeviceDetails):
        self.details = details

    def set_status(self, status: DeviceStatus):
        self.status = status

    def turn_on(self):
        self.broker.set_power(self.control_topic, PowerMode.ON)

    def turn_off(self):
        self.broker.set_power(self.control_topic, PowerMode.OFF)

    def set_temperature(self, temperature: float):
        self.broker.set_temperature(self.control_topic, temperature)

    def set_hvac_mode(self, mode: HVACMode):
        self.broker.set_hvac_mode(self.control_topic, mode)

    def set_fan_mode(self, mode: FanMode):
        self.broker.set_fan_mode(self.control_topic, mode)

    def set_preset_mode(self, mode: PresetMode):
        self.broker.set_preset_mode(self.control_topic, mode)

    def set_swing_mode(self, mode: SwingMode):
        self.broker.set_swing_mode(self.control_topic, mode)
