from google.cloud import iot_v1
from google.oauth2 import service_account

PROJECT_ID = "advnetworking"
CLOUD_REGION = "europe-west1"
REGISTRY_ID = "adv-networking-reg"

def updateDevice(deviceID, data):
    data = data.encode("utf-8")
    client = iot_v1.DeviceManagerClient()
    device_path = client.device_path(PROJECT_ID, CLOUD_REGION, REGISTRY_ID, "led-matrix")
    return client.modify_cloud_to_device_config(
        request={"name": device_path, "binary_data": data}
    )



#updateDevice("led-matrix", "ON BLUE")