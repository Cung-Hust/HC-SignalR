from Contracts.IHandler import IHandler
import logging
from Contracts.ITransport import ITransport
from Cache.GlobalVariables import GlobalVariables
import Constant.constant as const
from Database.Db import Db
from Model.userData import userData

import json
import sqlite3


def sql_update(cmd):
    con = sqlite3.connect("rd.Sqlite")
    cur = con.cursor()
    cur.execute(cmd)
    con.commit()
    con.close()


tokenTime = 0

#   ==============================================================================================


class MqttDataHandler(IHandler):
    __logger: logging.Logger
    __mqtt: ITransport
    __signalr: ITransport
    __globalVariables: GlobalVariables

    def __init__(self, log: logging.Logger, mqtt: ITransport, signalr: ITransport):
        self.__logger = log
        self.__mqtt = mqtt
        self.__globalVariables = GlobalVariables()
        self.__signalr = signalr

    def handler_signalr_command(self, item):
        pass

    def handler_signalr_response(self, item):
        pass

    def handler_mqtt_command(self, msg):
        self.__handler_topic_hc_control(msg)
        return

    def handler_mqtt_response(self, msg):
        self.__handler_topic_hc_control_response(msg)
        return

    def __handler_topic_hc_control_response(self, data):
        if self.__globalVariables.AllowChangeCloudAccountFlag:
            return
        if self.__globalVariables.PingCloudSuccessFlag:
            try:
                json_data = json.loads(data)
                cmd = json_data.get("CMD", "")
                dt = json_data.get("DATA", "")
                self.__hc_check_cmd_and_send_response_to_cloud(cmd, data)
                switcher = {
                    "DEVICE": self.__handler_cmd_device,
                    "DEVICE_UPDATE_STATUS": self.__handler_cmd_device_status,
                    "DEVICE_UPDATE": self.__handler_cmd_device,
                }
                func = switcher.get(cmd)
                func(dt)
            except:
                pass

    def __handler_topic_hc_control(self, data):
        print("\033[0;32mData - Topic HC.CONTROL:\n" + data)
        try:
            json_data = json.loads(data)
            cmd = json_data.get("CMD", "")
            dt = json_data.get("DATA", "")
            switcher = {
                "HC_CONNECT_TO_CLOUD": self.__handler_cmd_hc_connect_to_cloud,
                "RESET_HC": self.__handler_cmd_reset_hc,
                "UPDATE_FIRMWARE": self.__handler_cmd_update_firmware,
            }
            func = switcher.get(cmd)
            func(dt)
        except:
            pass

    def __handler_cmd_update_firmware(self, data):
        import subprocess
        import os
        import time

        print("\033[0;32mStart Update Firmware")
        self.__logger.info("Start Update Firmware")
        os.system("rm /root/*.xz")
        try:
            os.system("opkg update")
            os.system("pip3 install packaging")
            os.system("opkg update")
            os.system("opkg upgrade tar")
            file = open("/etc/version.txt", "r")
            current_ver = file.read().strip()
            print(f"Current version: {current_ver}")
            file.close()
            from packaging import version

            lastest_ver = data[-1]
            print(lastest_ver)
            lastest_ver_name = lastest_ver.get("NAME")
            print(lastest_ver_name)

            os.system("mkdir /etc/RECOVERY")
            os.system("rm /root/*.ipk")

            if version.parse(lastest_ver_name) > version.parse(current_ver):
                link = lastest_ver.get("URL")
                file_name = link[link.rfind("/") + 1 :]
                link_dl = "wget " + const.SERVER_HOST + link
                os.system(link_dl)

                process = subprocess.Popen(
                    ["sha256sum", f"{file_name}"],
                    stdout=subprocess.PIPE,
                    universal_newlines=True,
                )
                output = process.stdout.readline()
                src = output.strip()
                check_sum = lastest_ver.get("CHECK_SUM") + "  " + file_name
                if src == check_sum:
                    os.system(f"tar -xf {file_name}")

                    # move old file to dir /etc/RECOVERY
                    os.system("mv /root/RDhcPy/ /etc/RECOVERY")
                    os.system("mv /root/*.ipk /etc/RECOVERY")
                    os.system("mv /root/version.txt /etc/RECOVERY")
                    os.system(f"rm /root/{file_name}")

                    # move new file to dir root
                    os.system(f"mv /root/{lastest_ver_name}/* /root/")
                    os.system(f"rm -r /root/{lastest_ver_name}/")

                    # handle condition version required

                    file = open("/root/version.txt", "r")
                    str_ver = file.read().strip()
                    list_vers = str_ver.split("-")
                    print(list_vers)
                    file.close()

                    # required list version
                    req_list_vers = []
                    for ver in list_vers:
                        if version.parse(ver) > version.parse(current_ver):
                            req_list_vers.append(ver)
                    print(req_list_vers)

                    for req_ver in req_list_vers:
                        for d in data:
                            if req_ver == d.get("NAME"):
                                link_sub = d.get("URL")
                                file_sub_name = link_sub[link_sub.rfind("/") + 1 :]
                                link_sub_dl = "wget " + const.SERVER_HOST + link_sub
                                os.system(link_sub_dl)

                                process = subprocess.Popen(
                                    ["sha256sum", f"{file_sub_name}"],
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True,
                                )
                                output = process.stdout.readline()
                                src = output.strip()
                                print(src)
                                check_sum = d.get("CHECK_SUM") + "  " + file_sub_name
                                print(check_sum)
                                if src == check_sum:
                                    print("Start install sub-version")
                                    os.system(f"tar -xf /root/{file_sub_name}")

                                    # move old file to dir /etc/RECOVERY
                                    os.system("rm -r /etc/RECOVERY/*")
                                    os.system("mv /root/RDhcPy/ /etc/RECOVERY")
                                    os.system("mv /root/*.ipk /etc/RECOVERY")
                                    os.system("mv /root/version.txt /etc/RECOVERY")
                                    os.system(f"rm /root/{file_sub_name}")

                                    # move new file to dir root
                                    os.system(f"mv /root/{req_ver}/* /root/")
                                    os.system(f"rm -r /root/{req_ver}/")

                                    # install new file\
                                    os.system("opkg install /root/*.ipk")

                                    # delete /etc/RECOVERY
                                    os.system("rm -r /etc/RECOVERY/*")

                                    file = open("/etc/version.txt", "w")
                                    file.write(req_ver)
                                    file.close()
                                    os.system("chmod +x /root/config.sh")
                                    os.system("/root/config.sh")
                                    os.system("rm /root/config.sh")

                    time.sleep(4)
                    os.system("reboot -f")
        except:
            print("\033[0;31mCan Not Update Firmware")
            self.__logger.error("Can Not Update Firmware")

    def __handler_cmd_device(self, data):
        if self.__globalVariables.AllowChangeCloudAccountFlag:
            return
        signal_data = []
        try:
            for d in data:
                for i in d["PROPERTIES"]:
                    data_send_to_cloud = {
                        "deviceId": d["DEVICE_ID"],
                        "deviceAttributeId": i["ID"],
                        "value": i["VALUE"],
                    }
                    signal_data.append(data_send_to_cloud)
        except:
            self.__logger.error("\nData Attached With Device CMD Invalid")
            print("\033[0;31mData Attached With Device CMD Invalid")
            return

        if signal_data:
            size_arr = const.SIZE_OF_FRAME_DATA
            element = [
                signal_data[i : i + size_arr]
                for i in range(0, len(signal_data), size_arr)
            ]

            for i in range(len(element)):
                send_data = [
                    const.SIGNALR_CLOUD_RESPONSE_ENTITY,
                    json.dumps(element[i]),
                ]
                self.__signalr.send(self.__globalVariables.DormitoryId, send_data)
                print(
                    f"\033[0;35mData Send To HC-DeviceAttributeValue Entity:\n{json.dumps(element[i])}"
                )
                self.__logger.debug(
                    f"Data Send To HC-DeviceAttributeValue Entity:\n{json.dumps(element[i])}"
                )
        else:
            return

    def __handler_cmd_hc_connect_to_cloud(self, data):
        db = Db()
        dormitory_id = data.get("DORMITORY_ID", "")
        refresh_token = data.get("REFRESH_TOKEN", "")
        longitude = data.get("LONGITUDE")
        latitude = data.get("LATITUDE")

        if refresh_token != "":
            self.__globalVariables.RefreshToken = refresh_token
        self.__globalVariables.DormitoryId = dormitory_id

        self.__globalVariables.AllowChangeCloudAccountFlag = False

        user_data = userData(
            refreshToken=refresh_token,
            dormitoryId=dormitory_id,
            allowChangeAccount=False,
        )
        rel = db.Services.UserdataServices.FindUserDataById(id=1)
        dt = rel.first()
        if dt is not None:
            db.Services.UserdataServices.UpdateUserDataById(id=1, newUserData=user_data)
            cmd = (
                "UPDATE UserData SET Longitude = "
                + str(longitude)
                + ", Latitude = "
                + str(latitude)
                + " WHERE Id = 1 "
            )
            sql_update(cmd)
        if dt is None:
            db.Services.UserdataServices.AddNewUserData(newUserData=user_data)
            cmd = (
                "UPDATE UserData SET Longitude = "
                + str(longitude)
                + ", Latitude = "
                + str(latitude)
                + " WHERE Id = 1 "
            )
            sql_update(cmd)
            return

    def __handler_cmd_reset_hc(self, data):
        print("\033[0;33mAllow To Change Account. Now New Account Can Log In")
        self.__logger.info("Allow To Change Account. Now New Account Can Log In")

        db = Db()
        self.__globalVariables.AllowChangeCloudAccountFlag = True

        rel = db.Services.UserdataServices.FindUserDataById(id=1)
        dt = rel.first()
        if dt is None:
            return
        user_data = userData(
            refreshToken=self.__globalVariables.RefreshToken,
            dormitoryId=self.__globalVariables.DormitoryId,
            allowChangeAccount=self.__globalVariables.AllowChangeCloudAccountFlag,
        )

        db.Services.UserdataServices.UpdateUserDataById(id=1, newUserData=user_data)

    def __hc_check_cmd_and_send_response_to_cloud(self, cmd: str, data: str):
        room_response_cmd = [
            "CREATE_ROOM",
            "ADD_DEVICE_TO_ROOM",
            "REMOVE_DEVICE_FROM_ROOM",
        ]
        scene_response_cmd = ["CREATE_SCENE", "EDIT_SCENE"]
        if room_response_cmd.count(cmd) > 0:
            if data:
                size_arr = const.SIZE_OF_FRAME_DATA
                element = [
                    data[i : i + size_arr] for i in range(0, len(data), size_arr)
                ]

                for i in range(len(element)):
                    send_data = [
                        const.SIGNALR_APP_ROOM_RESPONSE_ENTITY,
                        json.dumps(element[i]),
                    ]
                    self.__signalr.send(self.__globalVariables.DormitoryId, send_data)
                    print(
                        f"\033[0;32mData Send To RoomResponse Entity:\n{json.dumps(element[i])}\n"
                    )
                    self.__logger.debug(
                        f"Data Send To RoomResponse Entity:\n{json.dumps(element[i])}\n"
                    )
            else:
                return
            return

        if scene_response_cmd.count(cmd) > 0:
            if data:
                size_arr = const.SIZE_OF_FRAME_DATA
                element = [
                    data[i : i + size_arr] for i in range(0, len(data), size_arr)
                ]

                for i in range(len(element)):
                    send_data = [
                        const.SIGNALR_APP_SCENE_RESPONSE_ENTITY,
                        json.dumps(element[i]),
                    ]
                    self.__signalr.send(self.__globalVariables.DormitoryId, send_data)
                    print(
                        f"\033[0;32mData Send To SceneResponse Entity:\n{json.dumps(element[i])}\n"
                    )
                    self.__logger.debug(
                        f"Data Send To SceneResponse Entity:\n{json.dumps(element[i])}\n"
                    )
            else:
                return
            return

        if (room_response_cmd + scene_response_cmd).count(cmd) == 0:
            if data:
                size_arr = const.SIZE_OF_FRAME_DATA
                element = [
                    data[i : i + size_arr] for i in range(0, len(data), size_arr)
                ]

                for i in range(len(element)):
                    send_data = [
                        const.SIGNALR_APP_DEVICE_RESPONSE_ENTITY,
                        json.dumps(element[i]),
                    ]
                    self.__signalr.send(self.__globalVariables.DormitoryId, send_data)
            else:
                return
            return

    def __handler_cmd_device_status(self, data):
        if self.__globalVariables.AllowChangeCloudAccountFlag:
            return

        if data:
            size_arr = const.SIZE_OF_FRAME_DATA
            element = [data[i : i + size_arr] for i in range(0, len(data), size_arr)]

            for i in range(len(element)):
                send_data = [
                    const.SIGNALR_CLOUD_RESPONSE_ENTITY,
                    json.dumps(element[i]),
                ]
                self.__signalr.send(self.__globalVariables.DormitoryId, send_data)
                print(
                    f"\033[0;32mDevice Status - ONLINE/OFFLINE - Cloud::\n{json.dumps(element[i])}\n"
                )
                self.__logger.debug(
                    f"Device Status - ONLINE/OFFLINE - Cloud::\n{json.dumps(element[i])}\n"
                )
        else:
            return
        return
