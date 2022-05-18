import paho.mqtt.client as mqtt
import asyncio
import queue
import Constant.constant as const
from Cache.GlobalVariables import GlobalVariables
import logging
import threading
import socket
from Contracts.ITransport import ITransport
import os.path
import ssl


def get_pwd():
    if os.path.isfile("/etc/PassMqtt.txt"):
        file = open("/etc/PassMqtt.txt", "r")
        pwd = file.read().strip()
        return pwd
    else:
        mqtts = "MQTTs"
        return mqtts


class MqttConfig:
    host: str
    port: int
    qos: int
    keep_alive: int
    username: str
    password: str

    def __init__(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        self.host = "localhost"
        self.port = const.MQTT_PORT
        self.qos = const.MQTT_QOS
        self.keep_alive = const.MQTT_KEEPALIVE
        self.username = const.MQTT_USER


class Mqtt(ITransport):
    __mqttConfig: MqttConfig
    __client: mqtt.Client
    __globalVariables: GlobalVariables
    __logger: logging.Logger
    __lock: threading.Lock

    def __init__(self, log: logging.Logger):
        super().__init__()
        self.__logger = log
        self.__mqttConfig = MqttConfig()
        self.__client = mqtt.Client()
        self.__globalVariables = GlobalVariables()
        self.__lock = threading.Lock()

    def __on_message(self, client, userdata, msg):
        message = msg.payload.decode("utf-8")
        topic = msg.topic
        item = {"topic": topic, "msg": message}
        with self.__lock:
            self.receive_response_data_queue.put(item)
            self.receive_command_data_queue.put(item)
        return

    def __on_connect(self, client, userdata, flags, rc):
        self.__client.subscribe(
            topic=const.MQTT_RESPONSE_TOPIC, qos=self.__mqttConfig.qos
        )
        self.__client.subscribe(
            topic=const.MQTT_CONTROL_TOPIC, qos=self.__mqttConfig.qos
        )

    def send(self, destination, send_data):
        try:
            self.__client.publish(destination, payload=send_data, qos=const.MQTT_QOS)
        except Exception as e:
            self.__client.reconnect()

    def disconnect(self):
        self.__client.disconnect()

    def connect(self):
        self.__client.on_message = self.__on_message
        self.__client.on_connect = self.__on_connect
        type_mqtt = get_pwd()
        if type_mqtt == "MQTTs":
            self.__client.tls_set(
                "/etc/mosquitto/ca.crt",
                tls_version=ssl.PROTOCOL_TLSv1_2,
            )
            self.__client.tls_insecure_set(True)
            self.__client.connect(self.__mqttConfig.host, 8883)

        else:
            self.__client.username_pw_set(
                username=self.__mqttConfig.username, password=get_pwd()
            )
            self.__client.connect(self.__mqttConfig.host, 1883)
        try:
            self.__client.loop_start()
        except Exception as err:
            self.__logger.error(f"Exception While Connecting MQTT: {err}")
            print(f"\033[0;31mException While Connecting Connect MQTT: {err}")

    def reconnect(self):
        pass

    def receive(self):
        pass
