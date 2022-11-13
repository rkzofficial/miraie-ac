from .device import Device


class Home:
    id: str
    devices: list[Device]

    def __init__(self, id: str, devices: list[Device]):
        self.id = id
        self.devices = devices

    def get_device(self, device_id: str):
        for device in self.devices:
            if device.id == device_id:
                return device
