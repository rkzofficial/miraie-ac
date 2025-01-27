import aiohttp
import asyncio

from . import constants
from .broker import MirAIeBroker
from .user import User
from .topic import MirAIeTopic
from .home import Home
from .device import Device, DeviceDetails, DeviceStatus
from .enums import PowerMode, FanMode, SwingMode, DisplayMode, HVACMode, PresetMode, ConvertiMode
from .utils import is_valid_email, toFloat
from .logger import LOGGER


class MirAIeHub:
    def __init__(self):
        self.http = aiohttp.ClientSession()
        self.topics_map: dict[str, MirAIeTopic] = {}
        self.background_tasks = set()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.http.close()

    def __build_headers__(self):
        return {
            "Authorization": f"Bearer {self.user.access_token}",
            "Content-Type": "application/json",
        }

    async def init(self, username: str, password: str, broker: MirAIeBroker):
        self._broker = broker

        await self._authenticate(username, password)
        await self._get_home_details()
        await self.get_all_device_status()
        await self._init_broker(broker)

    async def _init_broker(self, broker: MirAIeBroker):
        topics = self.get_device_topics()
        broker.set_topics(topics)
        loop = asyncio.get_event_loop()
        # Listen for mqtt messages in an (unawaited) asyncio task
        task = loop.create_task(
            broker.connect(self.home.id, self.user.access_token, self.get_token)
        )
        # Save a reference to the task so it doesn't get garbage collected
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.remove)

    @property
    def broker(self):
        return self._broker

    def get_device_topics(self):
        device_topics = list(
            map(
                lambda device: [device.status_topic, device.connection_status_topic],
                self.home.devices,
            )
        )
        miraie_topics = [topic for topics in device_topics for topic in topics]
        return miraie_topics

    async def get_token(self):
        try:
            await self._authenticate(self.username, self.password)
            return self.user.access_token
        except Exception:
            return self.user.access_token

    # Authenticate with the MirAIe API
    async def _authenticate(self, username: str, password: str):
        isEmail = is_valid_email(username)

        data = {
            "clientId": constants.httpClientId,
            "password": password,
            "scope": "an_14214235325",
        }

        if isEmail:
            data["email"] = username
        else:
            data["mobile"] = username

        response = await self.http.post(constants.loginUrl, json=data)

        if response.status == 200:
            json = await response.json()
            self.user = User(
                access_token=json["accessToken"],
                refresh_token=json["refreshToken"],
                user_id=json["userId"],
                expires_in=json["expiresIn"],
            )
            self.username = username
            self.password = password
            return True

        raise Exception("Authentication failed")

    # Get device details
    async def _get_device_details(self, deviceIds: str):
        response = await self.http.get(
            constants.deviceDetailsUrl + "/" + deviceIds,
            headers=self.__build_headers__(),
        )
        
        try:
            return await response.json()
        except aiohttp.ContentTypeError as error:
            LOGGER.error(f'_get_device_details error {error}', exc_info=True)
            LOGGER.debug(f'url: {response.url}')
            LOGGER.debug(f'status: {response.status}')
            LOGGER.debug(f'reason: {response.reason}')
            LOGGER.debug(f'content_type: {response.content_type}')
            LOGGER.debug(f'text response: {await response.text()}')
            raise Exception("Unable to fetch device details failed")
            

    # Process the home details
    async def _process_home_details(self, json_data):
        devices: list[Device] = []

        for space in json_data["spaces"]:
            for device in space["devices"]:
                item = Device(
                    id=device["deviceId"],
                    name=str(device["deviceName"]).lower().replace(" ", "-"),
                    friendly_name=device["deviceName"],
                    control_topic=str(device["topic"][0]) + "/control",
                    status_topic=str(device["topic"][0]) + "/status",
                    connection_status_topic=str(device["topic"][0])
                    + "/connectionStatus",
                    broker=self._broker,
                )
                devices.append(item)
                topic = MirAIeTopic(
                    control_topic=item.control_topic,
                    status_topic=item.status_topic,
                    connection_status_topic=item.connection_status_topic,
                )
                self.topics_map[item.id] = topic

        device_ids = ",".join(list(map(lambda device: device.id, devices)))
        device_details = await self._get_device_details(device_ids)

        for dd in device_details:
            device = next(d for d in devices if d.id == dd["deviceId"])

            details = DeviceDetails(
                model_name=dd["modelName"],
                mac_address=dd["macAddress"],
                category=dd["category"],
                brand=dd["brand"],
                firmware_version=dd["firmwareVersion"],
                serial_number=dd["serialNumber"],
                model_number=dd["modelNumber"],
                product_serial_number=dd["productSerialNumber"],
            )

            device.set_details(details)

        self.home = Home(id=json_data["homeId"], devices=devices)
        return self.home

    # Get home details
    async def _get_home_details(self):
        response = await self.http.get(
            constants.homesUrl, headers=self.__build_headers__()
        )
        resp = await response.json()
        await self._process_home_details(resp[0])

    # Get device status
    async def _get_device_status(self, device_id: str):
        response = await self.http.get(
            constants.statusUrl.replace("{deviceId}", device_id),
            headers=self.__build_headers__(),
        )
        resp = await response.json()
        resp["deviceId"] = device_id
        return resp

    # Get all device status
    async def get_all_device_status(self):
        statuses = await asyncio.gather(
            *[self._get_device_status(device.id) for device in self.home.devices],
            return_exceptions=True,
        )

        for status in statuses:
            device = next(d for d in self.home.devices if d.id == status["deviceId"])

            status_obj: DeviceStatus
            if "ty" not in status or status["ty"] != "AC":
                status_obj = DeviceStatus(
                    is_online=False,
                    temperature=24.0,
                    room_temperature=24.0,
                    power_mode=PowerMode.OFF,
                    fan_mode=FanMode.AUTO,
                    v_swing_mode=SwingMode.AUTO,
                    h_swing_mode=SwingMode.AUTO,
                    display_mode=DisplayMode.ON,
                    hvac_mode=HVACMode.AUTO,
                    preset_mode=PresetMode.NONE,
                    converti_mode=ConvertiMode.OFF,
                )
            else:
                status_obj = DeviceStatus(
                    is_online=status["onlineStatus"] == "true",
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
                    else PresetMode.NONE,
                    converti_mode=ConvertiMode(status.get("cnv", 0)),
                )

            device.set_status(status_obj)

        return statuses
