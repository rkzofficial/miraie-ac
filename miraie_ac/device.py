from typing import Callable
from .broker import MirAIeBroker
from .enums import PowerMode, FanMode, SwingMode, DisplayMode, HVACMode, PresetMode, ConvertiMode
from .utils import toFloat
from .logger import LOGGER


class DeviceStatus:
    def __init__(
        self,
        is_online: bool,
        temperature: float,
        room_temperature: float,
        power_mode: PowerMode,
        fan_mode: FanMode,
        v_swing_mode: SwingMode,
        h_swing_mode: SwingMode,
        display_mode: DisplayMode,
        hvac_mode: HVACMode,
        preset_mode: PresetMode,
        converti_mode: ConvertiMode,
    ):
        self.is_online = is_online
        self.temperature = temperature
        self.room_temperature = room_temperature
        self.power_mode = power_mode
        self.fan_mode = fan_mode
        self.v_swing_mode = v_swing_mode
        self.h_swing_mode = h_swing_mode
        self.display_mode = display_mode
        self.hvac_mode = hvac_mode
        self.preset_mode = preset_mode
        self.converti_mode = converti_mode
        LOGGER.debug(f"Device status: {self.__str__()}")
    
    def __str__(self):
        return (
            f"Is online? - {self.is_online}\n" +
            f"Temperature: {self.temperature}\n" +
            f"Room temperature: {self.room_temperature}\n" +
            f"Power mode: {self.power_mode}\n" +
            f"Fan mode: {self.fan_mode}\n" +
            f"Vertical swing mode: {self.v_swing_mode}\n" +
            f"Horizontal swing mode: {self.h_swing_mode}\n" +
            f"Display mode: {self.display_mode}\n" +
            f"Hvac mode: {self.hvac_mode}\n" +
            f"Preset mode: {self.preset_mode}\n" +
            f"Converti mode: {self.converti_mode}\n"
        )
        
    def __repr__(self):
        return self.__str__()

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
        LOGGER.debug(f"Device details: {self.__str__()}")
        
    def __str__(self):
        return (
            f"Brand: {self.brand}\n" +
            f"Category: {self.category}\n" +
            f"Model Name: {self.model_name}\n" +
            f"Model #: {self.model_number}\n" +
            f"MAC address: {self.mac_address}\n" +
            f"Firmware version: {self.firmware_version}\n" +
            f"Serial number: {self.serial_number}\n" +
            f"Model number: {self.model_number}\n" +
            f"Product serial number: {self.product_serial_number}\n"
        )
    
    def __repr__(self):
        return self.__str__()

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
        
    def __str__(self):
        return (
            f"Id: {self.id}\n" +
            f"Name: {self.name}\n" +
            f"Friendly name: {self.friendly_name}\n" +
            f"Control topic: {self.control_topic}\n" +
            f"Status topic: {self.status_topic}\n" +
            f"Connection status topic: {self.connection_status_topic}\n"
        )
        
    def __repr__(self):
        return self.__str__()

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
        LOGGER.debug(f"Raw device status: {status}")
        status_obj = DeviceStatus(
            is_online=self.status.is_online,
            temperature=toFloat(status["actmp"]),
            room_temperature=toFloat(status["rmtmp"]),
            power_mode=PowerMode(status["ps"]),
            fan_mode=FanMode(status["acfs"]),
            v_swing_mode=SwingMode(status["acvs"]),
            h_swing_mode=SwingMode(status["achs"]),
            display_mode=DisplayMode(status["acdc"]),
            hvac_mode=HVACMode(status["acmd"]),
            preset_mode=PresetMode.BOOST
            if status["acpm"] == "on"
            else PresetMode.ECO
            if status["acem"] == "on"
            else PresetMode.CLEAN
            if status["acec"] == "on"
            else PresetMode.NONE,
            converti_mode=ConvertiMode(status.get("cnv", 0)),
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

    async def turn_on(self):
        await self.broker.set_power(self.control_topic, PowerMode.ON)

    async def turn_off(self):
        await self.broker.set_power(self.control_topic, PowerMode.OFF)

    async def set_temperature(self, temperature: float):
        await self.broker.set_temperature(self.control_topic, temperature)

    async def set_hvac_mode(self, mode: HVACMode):
        await self.broker.set_hvac_mode(self.control_topic, mode)

    async def set_fan_mode(self, mode: FanMode):
        await self.broker.set_fan_mode(self.control_topic, mode)

    async def set_preset_mode(self, mode: PresetMode):
        await self.broker.set_preset_mode(self.control_topic, mode)

    async def set_v_swing_mode(self, mode: SwingMode):
        await self.broker.set_v_swing_mode(self.control_topic, mode)
        
    async def set_h_swing_mode(self, mode: SwingMode):
        await self.broker.set_h_swing_mode(self.control_topic, mode)
        
    async def set_display_mode(self, mode: DisplayMode):
        await self.broker.set_display_mode(self.control_topic, mode)
    
    async def set_converti_mode(self, mode: ConvertiMode):
        await self.broker.set_converti_mode(self.control_topic, mode)
