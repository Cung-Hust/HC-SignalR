from Contracts.ITransport import ITransport
from Contracts.IHandler import IHandler
import logging
from Cache.GlobalVariables import GlobalVariables
import Constant.constant as const


class SignalrDataHandler(IHandler):
    __logger: logging.Logger
    __mqtt: ITransport
    __signalr: ITransport
    __globalVariables: GlobalVariables

    def __init__(self, log: logging.Logger, mqtt: ITransport, signalr: ITransport):
        self.__logger = log
        self.__mqtt = mqtt
        self.__globalVariables = GlobalVariables()
        self.__signalr = signalr

    def handler_mqtt_command(self, item):
        pass

    def handler_mqtt_response(self, item):
        pass

    def handler_signalr_command(self, item):
        if self.__globalVariables.AllowChangeCloudAccountFlag:
            return

        dorId = item[0]
        entity = item[1]
        data = item[2]

        if dorId != self.__globalVariables.DormitoryId:
            return

        try:
            switcher = {
                const.SIGNALR_APP_COMMAND_ENTITY: self.__handler_log_signalr_command,
            }
            func = switcher.get(entity)
            func(item)
        except:
            pass
        return

    def handler_signalr_response(self, item):
        if self.__globalVariables.AllowChangeCloudAccountFlag:
            return

        dorId = item[0]
        entity = item[1]

        if dorId != self.__globalVariables.DormitoryId:
            return
        try:
            switcher = {
                const.SIGNALR_APP_DEVICE_RESPONSE_ENTITY: self.__handler_log_signalr_response,
                const.SIGNALR_APP_ROOM_RESPONSE_ENTITY: self.__handler_log_signalr_response,
                const.SIGNALR_APP_SCENE_RESPONSE_ENTITY: self.__handler_log_signalr_response,
                const.SIGNALR_CLOUD_RESPONSE_ENTITY: self.__handler_log_signalr_response,
            }
            func = switcher.get(entity)
            func(item)
        except:
            pass
        return

    def __handler_log_signalr_response(self, item):
        pass

    def __handler_log_signalr_command(self, item):
        entity = item[1]
        data = item[2]
        self.__logger.debug(f"SignalR Data - Command Entity: {data}")
        print(f"\033[0;32mSignalR Data - Command Entity:\n{data}")
        try:
            self.__mqtt.send(const.MQTT_CONTROL_TOPIC, data)
        except:
            pass
