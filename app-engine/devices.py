from google.cloud import iot_v1
from google.oauth2 import service_account
from google.cloud import pubsub_v1

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

def sensorCallback(message):
    data = message.data.decode("utf-8")
    if data == "Sensor is offline" or data == "Sensor is online":
        print(data)
    else:
        data = data.split(",")
        print('Temp: {}, Hum: {}, Pressure: {}'.format(data[0], data[1], data[2]))
    message.ack()

def pullSub(subID, callback):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, subID)

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")
    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result(timeout=5.0)
        except TimeoutError:
            streaming_pull_future.cancel()

#updateDevice("led-matrix", "ON BLUE")
#pullSub("sensors", sensorCallback)