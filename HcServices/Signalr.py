from signalrcore.hub_connection_builder import HubConnectionBuilder
import asyncio
import queue
import requests
from Cache.GlobalVariables import GlobalVariables
import Constant.constant as const
import logging
import threading
from Contracts.ITransport import ITransport
from Helper.System import System, eliminate_current_progress
import datetime
import time
import json
import sys


def get_token():
    cache = GlobalVariables()
    try:
        renew_token = const.SERVER_HOST + const.TOKEN_URL
        headers = {
            "Content-type": "application/json",
            "Accept": "text/plain",
            "X-DormitoryId": cache.DormitoryId,
            "Cookie": "RefreshToken={refresh_token}".format(
                refresh_token=cache.RefreshToken
            ),
        }
        response = requests.post(renew_token, json=None, headers=headers).json()
        token = response["token"]
        headers["Cookie"] = "Token={token}".format(token=token)
        return token
    except Exception as e:
        print(f"\033[0;31mException While Getting SignalR Token: {e}")
        logging.Logger.error(f"Exception While Getting SignalR Token: {e}")
        return None


class Signalr(ITransport):
    __hub: HubConnectionBuilder
    __globalVariables: GlobalVariables
    __logger: logging.Logger
    __lock: threading.Lock
    __mqtt: ITransport

    def __init__(self, log: logging.Logger):
        super().__init__()
        self.__logger = log
        self.__globalVariables = GlobalVariables()
        self.__lock = threading.Lock()
        self.__hub = None

    def __build_connection(self):
        self.__hub = (
            HubConnectionBuilder()
            .with_url(
                const.SERVER_HOST + const.SIGNALR_SERVER_URL,
                options={"access_token_factory": get_token, "headers": {}},
            )
            .build()
        )
        self.__hub.on_open(lambda: print("\033[1;32mConnect SignalR Successfully"))
        self.__hub.on_close(lambda: self.reconnect())
        return self

    def __on_receive_event(self):
        self.__hub.on("Receive", self.__receive_event_callback)

    def __receive_event_callback(self, data):
        with self.__lock:
            if data[1] == const.SIGNALR_APP_COMMAND_ENTITY:
                self.receive_command_data_queue.put(data)

    async def disconnect(self):
        try:
            self.__hub.stop()
        except:
            eliminate_current_progress()

    def send(self, destination, data_send):
        entity = data_send[0]
        message = data_send[1]
        try:
            if self.__globalVariables.SignalrConnectSuccessFlag == True:
                self.__hub.send("Send", [destination, entity, message])
        except:
            print("\033[0;31mCannot Send Data To Cloud")
            self.__globalVariables.SignalrConnectSuccessFlag == False
            self.__logger.error("Cannot Send Data To Cloud")

    async def connect(self):
        await asyncio.sleep(10)
        connect_success = False
        while self.__globalVariables.RefreshToken == "":
            await asyncio.sleep(1)
        while True:
            if (
                self.__globalVariables.PingGoogleSuccessFlag
                and not self.__globalVariables.SignalrConnectSuccessFlag
            ):
                try:
                    if self.__hub is not None:
                        self.__hub.stop()
                        self.__hub = None
                        print("\nClear SignalR Connect")
                    self.__build_connection()
                    connect_success = self.__hub.start()
                    if connect_success:
                        self.__on_receive_event()
                        self.__globalVariables.SignalrConnectSuccessFlag = True
                except Exception as err:
                    self.__logger.error(
                        f"Exception While Connecting Signalr to Server: {err}"
                    )
                    print(
                        f"\033[0;31mException While Connecting Signalr to Server: {err}"
                    )
                    eliminate_current_progress()
            await asyncio.sleep(3)

    def reconnect(self):
        print("\033[0;31mSignalr Disconnected")
        self.__logger.debug("Signalr Disconnected")
        self.__globalVariables.SignalrConnectSuccessFlag = False
        time.sleep(2)

    def receive(self):
        pass
