from HcServices.Http import Http
import asyncio
from Database.Db import Db
from Cache.GlobalVariables import GlobalVariables
import datetime
import logging
from Contracts.ITransport import ITransport
from Helper.System import (
    System,
    eliminate_current_progress,
    ping_google,
    check_and_kill_all_repeat_progress,
)
from Contracts.IHandler import IHandler
import Constant.constant as Const
import time
import json

current_weather = {}


class RdHc:
    __httpServices: Http
    __signalServices: ITransport
    __mqttServices: ITransport
    __globalVariables: GlobalVariables
    __logger: logging.Logger
    __mqttHandler: IHandler
    __signalrHandler: IHandler

    def __init__(
        self,
        log: logging.Logger,
        http: Http,
        signalr: ITransport,
        mqtt: ITransport,
        mqtt_handler: IHandler,
        signalr_handler: IHandler,
    ):
        self.__logger = log
        self.__httpServices = http
        self.__signalServices = signalr
        self.__mqttServices = mqtt
        self.__globalVariables = GlobalVariables()
        self.__mqttHandler = mqtt_handler
        self.__signalrHandler = signalr_handler

    # time between 2 consecutive pings is 60s(FPT requirement)
    # this time is detached: first 5s, second 55s(because of waiting to ping google)
    # cloud disconnect consecutive times max is 3(FPT requirement)
    async def __hc_check_connect_with_cloud(self):
        s = System(self.__logger)
        signalr_disconnect_count = 0
        signalr_disconnect_count_limit = 30
        first_success_ping_to_cloud_flag = False
        while True:
            await asyncio.sleep(5)
            print("\033[1;36mSend Heartbeat To Cloud")
            self.__logger.info("Send Heartbeat To Cloud")
            if self.__globalVariables.DisconnectTime is None:
                self.__globalVariables.DisconnectTime = datetime.datetime.now()

            self.__globalVariables.PingGoogleSuccessFlag = ping_google()

            if not self.__globalVariables.PingGoogleSuccessFlag:
                self.__globalVariables.PingCloudSuccessFlag = False

            if self.__globalVariables.PingGoogleSuccessFlag:
                self.__globalVariables.PingCloudSuccessFlag = (
                    s.send_http_request_to_heartbeat_url(self.__httpServices)
                )

            if not self.__globalVariables.PingCloudSuccessFlag:
                print("\033[1;31mCan Not Connect To Cloud")
                self.__logger.info("Can Not Connect To Cloud")
                signalr_disconnect_count = signalr_disconnect_count + 1
                print(
                    f"\033[1;33mSignalR Disconnect Count == {signalr_disconnect_count}"
                )
                self.__globalVariables.SignalrConnectSuccessFlag = False

            # Catch The Event The First Connect And Reconnect Cloud Successfully
            if self.__globalVariables.PingCloudSuccessFlag:
                s.recheck_reconnect_status_of_last_activation()
                if not first_success_ping_to_cloud_flag:
                    first_success_ping_to_cloud_flag = True
                    print("\033[1;32mCheck The First Time Connect To Cloud")
                    cmd = {"CMD": "DEVICE_UPDATE"}
                    self.__mqttServices.send(Const.MQTT_CONTROL_TOPIC, json.dumps(cmd))
                self.__globalVariables.DisconnectTime = None
                signalr_disconnect_count = 0
            else:
                first_success_ping_to_cloud_flag = False

            if signalr_disconnect_count == signalr_disconnect_count_limit:
                self.__hc_update_disconnect_status_to_db()
                eliminate_current_progress()

            await asyncio.sleep(50)

    def __hc_update_disconnect_status_to_db(self):
        self.__logger.info("Update Cloud Disconnect Status To DB")
        print("\033[1;32mUpdate Cloud Disconnect Status To DB")
        s = System(self.__logger)
        s.update_disconnect_status_to_db(self.__globalVariables.DisconnectTime)

    def __hc_handler_mqtt_control_data(self):
        if not self.__mqttServices.receive_command_data_queue.empty():
            item = self.__mqttServices.receive_command_data_queue.get()
            topic = item["topic"]
            msg = item["msg"]
            if topic == "HC.CONTROL":
                self.__mqttHandler.handler_mqtt_command(msg)
                self.__mqttServices.receive_command_data_queue.task_done()

    def __hc_handler_mqtt_response_data(self):
        if not self.__mqttServices.receive_response_data_queue.empty():
            item = self.__mqttServices.receive_response_data_queue.get()
            topic = item["topic"]
            msg = item["msg"]
            if topic == "HC.CONTROL.RESPONSE":
                self.__mqttHandler.handler_mqtt_response(msg)

    def __hc_handler_signalr_command_data(self):
        if not self.__signalServices.receive_command_data_queue.empty():
            item = self.__signalServices.receive_command_data_queue.get()
            self.__signalrHandler.handler_signalr_command(item)

    def __hc_handler_signalr_response_data(self):
        if not self.__signalServices.receive_response_data_queue.empty():
            item = self.__signalServices.receive_response_data_queue.get()
            self.__signalrHandler.handler_signalr_response(item)
            self.__signalServices.receive_response_data_queue.task_done()

    # report time interval is 1800(FPT requirements)
    async def __hc_report_online_status_to_cloud(self):
        await asyncio.sleep(5)
        report_time_interval = 500
        s = System(self.__logger)
        while True:
            if (
                self.__globalVariables.PingCloudSuccessFlag
                and not self.__globalVariables.AllowChangeCloudAccountFlag
            ):
                s.send_http_request_to_gw_online_status_url(self.__httpServices)
            await asyncio.sleep(report_time_interval)

    def __hc_get_gateway_mac(self):
        s = System(self.__logger)
        s.get_gateway_mac()

    # load refresh token and dormitoryId from db in runtime
    def __hc_load_user_data(self):
        db = Db()
        user_data = db.Services.UserdataServices.FindUserDataById(id=1)
        dt = user_data.first()
        if dt is not None:
            self.__globalVariables.DormitoryId = dt["DormitoryId"]
            self.__globalVariables.RefreshToken = dt["RefreshToken"]
            self.__globalVariables.AllowChangeCloudAccountFlag = dt[
                "AllowChangeAccount"
            ]

    # load current wifi SSID
    def __hc_load_current_wifi_name(self):
        s = System(self.__logger)
        s.update_current_wifi_name()

    # checking when wifi is changed
    async def __hc_check_wifi_change(self):
        s = System(self.__logger)
        while True:
            time.sleep(2)
            s.check_wifi_change()
            await asyncio.sleep(Const.HC_CHECK_WIFI_CHANGE_INTERVAL)

    def __get_weather(self):
        import os
        import time
        import requests
        import json

        os.system("ntpd -q -p 1.openwrt.pool.ntp.org")
        time.sleep(2)
        os.system("hwclock -w")

        db = Db()
        try:
            user_data = db.Services.UserdataServices.FindUserDataById(id=1)
            dt = user_data.first()
            if dt is not None:
                lat = dt["Latitude"]
                lon = dt["Longitude"]

            api_key = "9e5c3f896fa33c7bb5f5b457256320d0"
            # api_key = "05f40f1972e5ae4ff4fa2bbe2bd9adae"
            url = (
                "https://api.openweathermap.org/data/2.5/onecall?lat=%s&lon=%s&appid=%s&units=metric"
                % (lat, lon, api_key)
            )
            response = requests.get(url)
            data = json.loads(response.text)
            weather = data["current"]["weather"][0]
            cmd = {"cmd": "outWeather"}
            weather.update(cmd)
            temp = {"temp": data["current"]["temp"]}
            weather.update(temp)
            humi = {"humi": data["current"]["humidity"]}
            weather.update(humi)
            self.__mqttServices.send(Const.MQTT_CONTROL_TOPIC, json.dumps(weather))
            self.__globalVariables.CheckWeatherFlag = True
            self.__logger.info(f"Weather Info: {weather}")
        except:
            self.__logger.error(f"Can Not Get Weather Info")
            pass

    async def __hc_update_weather_status(self):
        while self.__globalVariables.PingGoogleSuccessFlag:
            try:
                print("\033[1;33mUpdate Weather Info")
                self.__get_weather()
                await asyncio.sleep(Const.HC_UPDATE_WEATHER_INTERVAL)
            except:
                pass

    def __check_the_first_connect_internet(self):
        ping_waiting_time = 10
        print("\033[1;33mCheck The First Internet Connection")
        send_weather_info_success_flag = False
        while not send_weather_info_success_flag:
            send_weather_info_success_flag = (
                self.__globalVariables.PingGoogleSuccessFlag
            )
            if self.__globalVariables.PingGoogleSuccessFlag:
                print("\033[1;33mConnect Internet Successfully !")
                if not self.__globalVariables.CheckWeatherFlag:
                    self.__get_weather()
                    self.__globalVariables.CheckWeatherFlag = True
                    return True
                else:
                    self.__globalVariables.CheckWeatherFlag = False
                    time.sleep(ping_waiting_time)

    async def __hc_check_service_status(self):
        import subprocess
        import os

        while True:
            count_service = 0

            process = subprocess.Popen(
                ["pgrep", "SYSTEM"], stdout=subprocess.PIPE, universal_newlines=True
            )
            output_1 = process.stdout.readlines()
            for line in output_1:
                count_service += 1

            process = subprocess.Popen(
                ["pgrep", "RD_SMART"], stdout=subprocess.PIPE, universal_newlines=True
            )
            output_2 = process.stdout.readlines()
            for line in output_2:
                count_service += 1

            if count_service == 2:
                os.system(
                    '/bin/echo "1" > /sys/class/leds/linkit-smart-7688:orange:service/brightness'
                )
            else:
                print("\033[1;31mService Fail")
                self.__logger.error("Service Fail")
                os.system(
                    '/bin/echo "0" > /sys/class/leds/linkit-smart-7688:orange:service/brightness'
                )

            await asyncio.sleep(Const.HC_CHECK_SERVICE_INTERVAL)

    def __hc_send_version_info(self):
        s = System(self.__logger)
        send_version_success_flag = False
        while not send_version_success_flag:
            try:
                s.update_firmware_version_info_to_cloud(self.__httpServices)
                send_version_success_flag = True
            except Exception as e:
                print(f"\033[1;31mError updating firmware version: {e}")
                self.__logger.error(f"\033[1;31mError updating firmware version: {e}")
                pass

    async def __process_command(self):
        while True:
            self.__hc_handler_signalr_command_data()
            self.__hc_handler_mqtt_control_data()
            time.sleep(0.01)

    async def __process_response(self):
        while True:
            self.__hc_handler_mqtt_response_data()
            self.__hc_handler_signalr_response_data()
            time.sleep(0.01)

    async def program_1(self):
        check_and_kill_all_repeat_progress()
        self.__hc_get_gateway_mac()
        self.__hc_load_user_data()
        self.__hc_load_current_wifi_name()
        self.__check_the_first_connect_internet()
        self.__hc_send_version_info()
        task0 = asyncio.create_task(self.__hc_check_wifi_change())
        task1 = asyncio.create_task(self.__hc_check_service_status())
        task2 = asyncio.create_task(self.__hc_update_weather_status())
        tasks = [task0, task1, task2]
        await asyncio.gather(*tasks)

    async def program_2(self):
        task0 = asyncio.create_task(self.__hc_check_connect_with_cloud())
        task1 = asyncio.create_task(self.__hc_report_online_status_to_cloud())
        tasks = [task0, task1]
        await asyncio.gather(*tasks)

    async def program_3(self):
        task0 = asyncio.create_task(self.__process_command())
        tasks = [task0]
        await asyncio.gather(*tasks)

    async def program_4(self):
        task0 = asyncio.create_task(self.__process_response())
        tasks = [task0]
        await asyncio.gather(*tasks)
