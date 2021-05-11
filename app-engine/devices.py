from google.cloud import iot_v1
from google.cloud import pubsub_v1
from google.api_core import retry
import datetime
import pytz

PROJECT_ID = "advnetworking"
CLOUD_REGION = "europe-west1"
REGISTRY_ID = "adv-networking-reg"

utc=pytz.UTC

def updateDevice(deviceID, data):
    data = data.encode("utf-8")
    client = iot_v1.DeviceManagerClient()
    device_path = client.device_path(PROJECT_ID, CLOUD_REGION, REGISTRY_ID, "led-matrix")
    return client.modify_cloud_to_device_config(
        request={"name": device_path, "binary_data": data}
    )

def pullSub(subID):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, subID)

    #print("Listening for messages on {}..".format(subscription_path))
    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 5},
            retry=retry.Retry(deadline=200)
        )
        ack_ids = []
        latestTime = datetime.datetime(2000, 7, 12).replace(tzinfo=utc) #Want to keep lastest message so that can tell if device is online or not
        lastestAck = ""
        lastestMsg = ""
        for received_message in response.received_messages:
            data = received_message.message.data.decode("utf-8")
            ack_ids.append(received_message.ack_id)
            time = received_message.message.publish_time.replace(tzinfo=utc)
            if(time > latestTime):
                latestTime = time
                lastestAck = received_message.ack_id
                lastestMsg = data

        # Acknowledges the received messages so they will not be sent again.
        if len(ack_ids) > 1:
            ack_ids.remove(lastestAck)
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )
            
        return lastestMsg

#updateDevice("led-matrix", "ON BLUE")
#print(pullSub("sensors"))