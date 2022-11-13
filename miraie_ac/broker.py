from paho.mqtt import client as mqtt
import ssl
import certifi
import random
import json


class MirAIeBroker:
    host = "mqtt.miraie.in"
    port = 8883
    use_ssl = True
    client_id = f"ha-mirae-mqtt-{random.randint(0, 1000)}"

    def set_topics(self, topics: list[str]):
        self.commandTopics = topics

    def on_connect(self, client: mqtt.Client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribe to all command topics
        for topic in self.commandTopics:
            client.subscribe(topic)

    def on_message(self, client: mqtt.Client, userdata, msg):
        pass
        # print(msg.topic)
        # parsed = json.loads(msg.payload.decode("utf-8"))
        # print(json.dumps(parsed, indent=4))

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection.")

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

    def build_base_payload(self):
        return {
            "ki": 1,
            "cnt": "an",
            "sid": "1",
        }

    def build_power_payload(self, power: str):
        payload = self.build_base_payload()
        payload["ps"] = str(power)
        return payload

    def build_temperature_payload(self, temperature: float):
        payload = self.build_base_payload()
        payload["actmp"] = str(temperature)
        return payload

    def set_temperature(self, topic: str, temperature: float):
        payload_str = json.dumps(self.build_temperature_payload(temperature))
        self.client.publish(topic, payload_str)

    def turn_on(self, topic: str):
        payload_str = json.dumps(self.build_power_payload("on"))
        self.client.publish(topic, payload_str)

    def turn_off(self, topic: str):
        payload_str = json.dumps(self.build_power_payload("off"))
        self.client.publish(topic, payload_str)
