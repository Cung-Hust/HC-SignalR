HttpStatusCodeOk = 200

# Cloud generic information
# SERVER_HOST = "https://iot-dev.truesight.asia"
SERVER_HOST = "https://rallismartv2.rangdong.com.vn"

# SignalR connection option
SIGNALR_SERVER_URL = "/rpc/iot-ebe/signalr/sync"
SIGNSLR_HEARDBEAT_URL = "/rpc/iot-ebe/sync/time"
SIGNALR_GW_HEARTBEAT_URL = "/rpc/iot-ebe/sync/hc/ping"
SIGNALR_APP_COMMAND_ENTITY = "Command"
SIGNALR_APP_DEVICE_RESPONSE_ENTITY = "DeviceResponse"
SIGNALR_APP_ROOM_RESPONSE_ENTITY = "RoomResponse"
SIGNALR_APP_SCENE_RESPONSE_ENTITY = "SceneResponse"
SIGNALR_CLOUD_RESPONSE_ENTITY = "HC-DeviceAttributeValue"
SIGNALR_UPDATE_FIRMWARE_URL = "/rpc/iot-ebe/sync/hc/update-version"

# pull,push data url
CLOUD_PUSH_DATA_URL = "/rpc/iot-ebe/sync/hc/merge-device-attribute-value"

# Server connection option
TOKEN_URL = "/rpc/iot-ebe/account/renew-token"

# Mqtt connection option
MQTT_PORT = 1883
MQTT_QOS = 2
MQTT_KEEPALIVE = 60
MQTT_CONTROL_TOPIC = "HC.CONTROL"
MQTT_RESPONSE_TOPIC = "HC.CONTROL.RESPONSE"
MQTT_USER = "RD"

# Sqlite connection option
DB_NAME = "rd.Sqlite"

# Check ext
HC_UPDATE_WEATHER_INTERVAL = 3600
HC_CHECK_SERVICE_INTERVAL = 60
HC_CHECK_WIFI_CHANGE_INTERVAL = 60

SIZE_OF_FRAME_DATA = 60
