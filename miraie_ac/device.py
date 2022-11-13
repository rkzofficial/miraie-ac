from .broker import MirAIeBroker


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

    def set_details(self, details: DeviceDetails):
        self.details = details

    def turn_on(self):
        self.broker.turn_on(self.control_topic)

    def turn_off(self):
        self.broker.turn_off(self.control_topic)

    def set_temperature(self, temperature: float):
        self.broker.set_temperature(self.control_topic, temperature)
