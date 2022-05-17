from Helper.Terminal import execute, execute_with_result
from Database.Db import Db
from Model.systemConfiguration import systemConfiguration
from Cache.GlobalVariables import GlobalVariables
import datetime
from HcServices.Http import Http
from Contracts.ITransport import ITransport
from sqlalchemy import and_, or_
from HcServices.Http import Http
import Constant.constant as const
import http
import json
import logging

import re
import uuid
import time


def time_split(time: datetime.datetime):
    m = str(time.month)
    if int(m) < 10:
        m = "0" + m

    d = str(time.day)
    if int(d) < 10:
        d = "0" + d

    update_day = int(str(time.year) + m + d)
    update_time = 60 * time.hour + time.minute
    return update_day, update_time


def ping_google():
    rel = execute_with_result("ping -c3 www.google.com|grep packet")[1]
    try:
        rel2 = rel.split(", ")
        rel3 = rel2[2].split(" ")
        r = rel3[0] == "0%"
    except:
        r = False
        print("\033[0;31mCan Not Ping To Google !!!")
    return r


def eliminate_current_progress():
    print(f"\033[0;33mThis Program Is Killed Now")
    s = execute_with_result(f"ps | grep python3")
    dt = s[1].split(" ")
    current_progress_port = ""
    for i in range(len(dt)):
        if dt[i] != "":
            current_progress_port = dt[i]
            break
    print(f"\033[0;33mkill -9 {current_progress_port}")
    time.sleep(3)
    execute(f"kill -9 {current_progress_port}")


def check_and_kill_all_repeat_progress():
    s = execute_with_result(f"ps|grep python3")
    current_self_repeat_process_list_info = s[1].split("\n")
    current_self_repeat_process_list_port = []
    for i in range(len(current_self_repeat_process_list_info)):
        p = current_self_repeat_process_list_info[i].split(" ")
        if p[len(p) - 1] != "RDhcPy/main.py":
            continue
        current_self_repeat_process_list_port.append(p[1])

    if len(current_self_repeat_process_list_port) > 1:
        kill_all_cmd = "kill -9"
        for i in range(len(current_self_repeat_process_list_port)):
            kill_all_cmd = kill_all_cmd + " " + current_self_repeat_process_list_port[i]
        execute(kill_all_cmd)


class System:
    __db = Db()
    __globalVariables = GlobalVariables()
    __logger = logging.Logger

    def __init__(self, logger: logging.Logger):
        self.__logger = logger

    def get_gateway_mac(self):
        mac_len = 17
        s = execute_with_result("ifconfig")
        dt = s[1].split("\n")
        for i in dt:
            if str(i).find("eth0") != -1:
                last_mac_character = len(i) - 2
                self.__globalVariables.GatewayMac = i[
                    last_mac_character - mac_len : last_mac_character
                ]
                break
        return

    def send_http_request_to_gw_online_status_url(self, h: Http):
        token = self.__get_token(h)
        cookie = f"Token={token}"
        heartbeat_url = const.SERVER_HOST + const.SIGNALR_GW_HEARTBEAT_URL
        header = h.create_new_http_header(
            cookie=cookie, domitory_id=self.__globalVariables.DormitoryId
        )
        mac = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        gw_report_body_data = {"macAddress": mac}
        req = h.create_new_http_request(
            url=heartbeat_url, header=header, body_data=gw_report_body_data
        )
        try:
            res = h.post(req)
            data = res.json()
            self.__logger.info(f"Ping Cloud Status: {data}")
            print(f"\033[1;33mPing Cloud Status: {data}")
        except:
            print(f"\033[0;31mCan Not Ping To Cloud")
            self.__logger.debug(f"Can Not Ping To Cloud")
            pass

    def update_current_wifi_name(self):
        s = execute_with_result("iwinfo")
        dt = s[1].split("\n")
        if str(dt[0]).find("RD_HC") == -1:
            wifi_name_started_point = str(dt[0]).find('"') + 1
            wifi_name_ended_point = str(dt[0]).find('"', wifi_name_started_point) - 1
            self.__globalVariables.CurrentWifiName = str(dt[0])[
                wifi_name_started_point : wifi_name_ended_point + 1
            ]
            print(
                f"\033[1;33mCurrent Wifi's Name: {self.__globalVariables.CurrentWifiName}"
            )
            self.__logger.info(
                f"Current Wifi's Name: {self.__globalVariables.CurrentWifiName}"
            )

    def check_wifi_change(self):
        s = execute_with_result("iwinfo")
        dt = s[1].split("\n")
        wifi_name = ""
        if str(dt[0]).find("RD_HC") == -1:
            wifi_name_started_point = str(dt[0]).find('"') + 1
            wifi_name_ended_point = str(dt[0]).find('"', wifi_name_started_point) - 1
            wifi_name = str(dt[0])[wifi_name_started_point : wifi_name_ended_point + 1]
        if wifi_name != "" and wifi_name != self.__globalVariables.CurrentWifiName:
            self.__logger.info(
                f"Current Wifi Change From {self.__globalVariables.CurrentWifiName} To {wifi_name}"
            )
            print(
                f"\033[0;33mCurrent Wifi Change From {self.__globalVariables.CurrentWifiName} To {wifi_name}"
            )
            time.sleep(5)
            print(f"\033[0;33mCheck Wifi Change ???")
            eliminate_current_progress()

    def update_reconnect_status_to_db(self, reconnect_time: datetime.datetime):
        rel = self.__db.Services.SystemConfigurationServices.FindSysConfigurationById(
            id=1
        )
        r = rel.fetchone()
        s = systemConfiguration(
            IsConnect=True,
            DisconnectTime=r["DisconnectTime"],
            ReconnectTime=reconnect_time,
            IsSync=r["IsSync"],
        )
        self.__db.Services.SystemConfigurationServices.UpdateSysConfigurationById(
            id=1, sysConfig=s
        )
        self.__push_data_to_cloud(r["DisconnectTime"], s)

    def update_disconnect_status_to_db(self, disconnect_time: datetime.datetime):
        s = systemConfiguration(
            IsConnect=False,
            DisconnectTime=disconnect_time,
            ReconnectTime=None,
            IsSync=False,
        )
        if disconnect_time is None:
            s.DisconnectTime = datetime.datetime.now()
        rel = self.__db.Services.SystemConfigurationServices.FindSysConfigurationById(
            id=1
        )
        r = rel.fetchone()
        if r is None:
            self.__db.Services.SystemConfigurationServices.AddNewSysConfiguration(s)
        if r is not None and r["IsSync"] != "False":
            self.__db.Services.SystemConfigurationServices.UpdateSysConfigurationById(
                id=1, sysConfig=s
            )

    def recheck_reconnect_status_of_last_activation(self):
        if not self.__globalVariables.RecheckConnectionStatusInDbFlag:
            rel = (
                self.__db.Services.SystemConfigurationServices.FindSysConfigurationById(
                    id=1
                )
            )
            r = rel.fetchone()

            if r is None:
                s = systemConfiguration(
                    IsConnect=True,
                    DisconnectTime=datetime.datetime.now(),
                    ReconnectTime=datetime.datetime.now(),
                    IsSync=True,
                )
                self.__db.Services.SystemConfigurationServices.AddNewSysConfiguration(s)
                self.__globalVariables.RecheckConnectionStatusInDbFlag = True
                return

            s = systemConfiguration(
                IsConnect=r["IsConnect"],
                DisconnectTime=r["DisconnectTime"],
                ReconnectTime=r["ReconnectTime"],
                IsSync=r["IsSync"],
            )

            if r["ReconnectTime"] is None:
                reconnectTime = datetime.datetime.now()
                self.update_reconnect_status_to_db(reconnectTime)
                s.ReconnectTime = reconnectTime
                s.IsConnect = True
                ok = self.__push_data_to_cloud(r["DisconnectTime"], s)
                if ok:
                    self.__globalVariables.RecheckConnectionStatusInDbFlag = True
                return

            if r["ReconnectTime"] is not None and r["IsSync"] == "False":
                s.IsConnect = True
                ok = self.__push_data_to_cloud(r["DisconnectTime"], s)
                if ok:
                    self.__globalVariables.RecheckConnectionStatusInDbFlag = True
                return
        self.__globalVariables.RecheckConnectionStatusInDbFlag = True
        return

    def send_http_request_to_heartbeat_url(self, h: Http):
        heartbeat_url = const.SERVER_HOST + const.SIGNSLR_HEARDBEAT_URL
        header = h.create_new_http_header(
            cookie="", domitory_id=self.__globalVariables.DormitoryId
        )
        req = h.create_new_http_request(url=heartbeat_url, header=header)
        try:
            res = h.post(req)
            if res.status_code == 200:
                return True
            else:
                return False
        except:
            print("\033[0;31mHTTP Error While Sending Heartbeat")
            return False

    def __get_token(self, http: Http):
        refresh_token = self.__globalVariables.RefreshToken
        if refresh_token == "":
            return ""
        token_url = const.SERVER_HOST + const.TOKEN_URL
        cookie = f"RefreshToken={refresh_token}"
        header = http.create_new_http_header(
            cookie=cookie, domitory_id=self.__globalVariables.DormitoryId
        )
        req = http.create_new_http_request(url=token_url, header=header)
        token = ""
        try:
            res = http.post(req).json()
            if res != "":
                try:
                    token = res["token"]
                except:
                    return ""
        except:
            pass
        return token

    def __push_data_to_cloud(
        self, reference_time: datetime.datetime, dt: systemConfiguration
    ):
        t = time_split(time=reference_time)
        update_day = t[0]
        update_time = t[1]
        print(f"\033[0;33mUpdate Day: {update_day}, Update Time: {update_time}")

        rel = self.__db.Services.DeviceAttributeValueServices.FindDeviceAttributeValueWithCondition(
            or_(
                and_(
                    self.__db.Table.DeviceAttributeValueTable.c.UpdateDay == update_day,
                    self.__db.Table.DeviceAttributeValueTable.c.UpdateTime
                    >= update_time,
                ),
                self.__db.Table.DeviceAttributeValueTable.c.UpdateDay > update_day,
            )
        )
        data = []
        for r in rel:
            if (
                r["DeviceId"] == ""
                or r["DeviceAttributeId"] is None
                or r["Value"] is None
            ):
                continue
            d = {
                "deviceId": r["DeviceId"],
                "deviceAttributeId": r["DeviceAttributeId"],
                "value": r["Value"],
            }
            data.append(d)
        if not data:
            self.__update_sync_data_status_success_to_db(dt)
            return True

        data_send_to_cloud = json.dumps(data)
        print(f"\033[0;32mData Push To Cloud: {data_send_to_cloud}")
        res = self.__send_http_request_to_push_url(data=data_send_to_cloud)
        print(f"\033[0;32mPush Data Action Response: {res}")
        self.__logger.info(f"Push Data Action Response: {res}")
        if res == "":
            print("\033[0;31mCan Not Push Data To Cloud")
            self.__logger.info("Can Not Push Data To Cloud")
            self.__update_sync_data_status_fail_to_db(dt)
            return False

        if (res != "") and (res.status == http.HTTPStatus.OK):
            self.__update_sync_data_status_success_to_db(dt)
            print("\033[0;32mPush Data Successfully")
            self.__logger.info("Push Data Successfully")
            return True

        print("\033[0;31mPush Data Failure")
        self.__logger.info("Push Data Failure")
        self.__update_sync_data_status_fail_to_db(dt)
        return False

    def __send_http_request_to_push_url(self, data: str):
        h = Http()
        token = self.__get_token(h)
        cookie = f"Token={token}"
        pull_data_url = const.SERVER_HOST + const.CLOUD_PUSH_DATA_URL
        header = h.create_new_http_header(
            cookie=cookie, domitory_id=self.__globalVariables.DormitoryId
        )
        req = h.create_new_http_request(
            url=pull_data_url, body_data=json.loads(data), header=header
        )
        try:
            res = h.post(req)
            return res
        except:
            pass

    def __update_sync_data_status_success_to_db(self, s: systemConfiguration):
        s.IsSync = True
        self.__db.Services.SystemConfigurationServices.UpdateSysConfigurationById(
            id=1, sysConfig=s
        )

    def __update_sync_data_status_fail_to_db(self, s: systemConfiguration):
        s.IsSync = False
        self.__db.Services.SystemConfigurationServices.UpdateSysConfigurationById(
            id=1, sysConfig=s
        )

    def update_firmware_version_info_to_cloud(self, h: Http):
        import re
        import uuid

        token = self.__get_token(h)
        cookie = f"Token={token}"
        update_firmware_url = const.SERVER_HOST + const.SIGNALR_UPDATE_FIRMWARE_URL
        header = h.create_new_http_header(
            cookie=cookie, domitory_id=self.__globalVariables.DormitoryId
        )
        file = open("/etc/version.txt", "r")
        current_ver = file.read().strip()
        file.close()
        mac = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        firmware_report_body_data = {
            "macAddress": mac,
            "version": current_ver,
            "dormitoryId": self.__globalVariables.DormitoryId,
        }
        print(f"\033[0;33mUpdate Firmware Info To Cloud: {firmware_report_body_data}")
        self.__logger.debug(
            f"Update Firmware Info To Cloud: {firmware_report_body_data}"
        )
        req = h.create_new_http_request(
            url=update_firmware_url, header=header, body_data=firmware_report_body_data
        )
        try:
            res = h.post(req)
            self.__logger.info(f"Update Firmware Status: {res.json()}")
            print(f"\033[1;33mUpdate Firmware Status: {res.json()}")
        except:
            self.__logger.error(f"Can Not Update Firmware Info")
            pass
