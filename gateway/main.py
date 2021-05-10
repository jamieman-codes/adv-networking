import paho.mqtt.client as mqtt
import ssl
import datetime
import jwt
import socket
import time
from time import ctime
import json


#Constants
REGISTRY_ID = "adv-networking-reg" #Cloud IoT core registry name
GATEWAY_ID = "rasp-pi" #Cloud IoT core gateway name
CLOUD_REGION = "europe-west1" #GCP Cloud region
PROJECT_ID = "advnetworking" #GCP Project name
PRIV_KEY = "jwtRS256.key" #Path to private key
ALGORITHM = "RS256" #Which algorithim to use to generate JWT
CERT = "roots.pem" #CA roots
MQTT_BRIDGE_HOST = "mqtt.googleapis.com" #MQTT Bridge hostname
MQTT_BRIDGE_PORT = 8883 #MQTT Bridge port
JWT_EXPIRE = 1200 #JWT expiration time (Mins)

HOST = ''
PORT = 10000
BUFSIZE = 2048
ADDR = (HOST, PORT)
MAX_BACKOFF_TIME = 32 #The maximum backoff time before giving up

COLOURS = ["WHITE", "RED", "BLUE", "GREEN", "PURPLE", "YELLOW", "TURQUOISE", "ORANGE", "PINK", "BROWN", "BLACK"]

class State:
    mqttConfigTopic = '/devices/{}/config'.format(GATEWAY_ID) # This is the topic that the device will receive configuration updates on.
    mqttErrorTopic = '/devices/{}/errors'.format(GATEWAY_ID)  # This is the topic that the device will receive configuration updates on.
 
    subscriptions = {} #The key is subscription topic. The value is the IP of device that is subscribed

    backoff = False #Whether to backoff before publishing
    minBackoffTime = 1 # The initial backoff time after a disconnection occurs


#Create state and socket
gatewayState = State()
udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#Creates a JWT used to establish connect to the MQTT bridge
def create_jwt():
    print('Creating JWT from {}'.format(PRIV_KEY))
    token = {
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRE),
        'aud': PROJECT_ID
    }
    with open(PRIV_KEY, 'r') as f:
        return jwt.encode(token, f.read(), algorithm=ALGORITHM)

#Convert paho error to human readable str
def paho_error(rc):
    return '{}: {}'.format(rc, mqtt.error_string(rc))

def on_connect(client, unused_userdata, unused_flags, rc):
    print('on_connect', mqtt.connack_string(rc))
    client.subscribe(gatewayState.mqttConfigTopic, qos=1)
    client.subscribe(gatewayState.mqttErrorTopic, qos=0)
    gatewayState.backoff = False
    gatewayState.minBackoffTime = 1

def on_disconnect(client, unused_userdata, rc):
    print('on_disconnect', paho_error(rc))
    gatewayState.backoff = True

def on_publish(unused_client, userdata, mid):
    print('published: {}'.format(userdata))

def on_subscribe(unused_client, unused_userdata, mid, granted_qos):
    print('on_subscribe: mid {}, qos {}'.format(mid, granted_qos))

#Callback when the device receives a message on a subscription
def on_message(unused_client, unused_userdata, message):
    payload = message.payload.decode('utf8')
    print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
            payload, message.topic, str(message.qos)))

    try:
        clientAddr = gatewayState.subscriptions[message.topic]
        print('Relaying config[{}] to {}'.format(payload, clientAddr))
        #Validate message:
        payloadSplit = payload.split(" ")
        payloadEncoded = payload.rstrip().encode('utf8')
        if payloadSplit[0] == "ON":
            if payloadSplit[1] == "MATRIX": #Example matrix command: ON MATRIX BLUE,GREEN,BLUE,YELLOW etc.. for 64 length
                matrix = payloadSplit[2].split(",")
                if len(matrix) != 64:
                    print('Matrix invalid length')
                else:
                    for colour in matrix:
                        if colour not in COLOURS:
                            print("Invalid colour in matrix: {}".format(colour))
                            return
                    udpSerSock.sendto(payloadEncoded, clientAddr)
            elif payloadSplit[1] in COLOURS:
                udpSerSock.sendto(payloadEncoded, clientAddr)
            else:
                print('Unrecognized command: {}'.format(payload))
        elif payloadSplit[0] == "OFF":
            udpSerSock.sendto(payloadEncoded, clientAddr)
        else:
            print('Unrecognized command: {}'.format(payload))
    except KeyError:
        print('Nobody subscribes to topic {}'.format(message.topic))
    except IndexError:
        print("Invalid command: {}".format(payload))

#Create paho MQTT client
def create_client():
    #Client_id is used to indentify the gateway device
    client = mqtt.Client(client_id=('projects/{}/locations/{}/registries/{}/devices/{}'.format(PROJECT_ID, CLOUD_REGION, REGISTRY_ID, GATEWAY_ID)))
    #Username is ignored by GCloud, JWT is used to authenticate
    client.username_pw_set(username="", password=create_jwt())
    # Enable SSL/TLS support.
    client.tls_set(ca_certs=CERT, tls_version=ssl.PROTOCOL_TLSv1_2)
    #Register callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    #Connect to MQTT Bridge
    client.connect(MQTT_BRIDGE_HOST, MQTT_BRIDGE_PORT)
    #Publish that gateway has started
    client.publish('/devices/{}/events'.format(GATEWAY_ID), 'Pi Gateway started', qos=0)
    return client 

def main():
    #Setup
    client = create_client()

    #Create UDP socket
    udpSerSock.setblocking(False)
    udpSerSock.bind(ADDR)
    
    #Main loop
    while True:
        client.loop()

        if gatewayState.backoff: #Try to reconnect 
            if gatewayState.minBackoffTime > MAX_BACKOFF_TIME:
                print('Exceeded maximum backoff time.')
                break
            print("Cannot connect. Backing off for: {}".format(gatewayState.minBackoffTime))
            time.sleep(gatewayState.minBackoffTime)
            gatewayState.minBackoffTime *= 2
            client.connect(MQTT_BRIDGE_HOST, MQTT_BRIDGE_PORT)

        #Try to get data from socket
        try:
            data, clientAddr = udpSerSock.recvfrom(BUFSIZE)
        except socket.error:
            continue
        print('[{}]: From Address {}:{} receive data: {}'.format(
                ctime(), clientAddr[0], clientAddr[1], data.decode("utf-8")))

        #Convert to json
        command = json.loads(data.decode('utf-8'))
        if not command:
            print('invalid json command {}'.format(data))
            continue

        action = command["action"]
        deviceID = command["device"]
        template = '{{ "device": "{}", "command": "{}", "status" : "ok" }}'

        if action == 'event': #Publishes telemetry data to pub/sub
            print('Sending telemetry event for device {}'.format(deviceID))
            payload = command["data"]

            mqttTopic = '/devices/{}/events'.format(deviceID)
            print('Publishing message to topic {} with payload \'{}\''.format(mqttTopic, payload))
            client.publish(mqttTopic, payload, qos=0) 

            message = template.format(deviceID, 'event')
            udpSerSock.sendto(message.encode('utf8'), clientAddr)

        elif action == 'attach': #Attaches a device to the gateway
            print('Sending telemetry event for device {}'.format(deviceID))
            attachTopic = '/devices/{}/attach'.format(deviceID)

            print('Attaching device {}'.format(deviceID))
            print(attachTopic)
            client.publish(attachTopic, "", qos=1)

            message = template.format(deviceID, 'attach')
            udpSerSock.sendto(message.encode('utf8'), clientAddr)

        elif action == "subscribe": #Subscribes a device to the config for that device
            print('subscribe config for {}'.format(deviceID))
            subscribe_topic = '/devices/{}/config'.format(deviceID)

            client.subscribe(subscribe_topic, qos=1)
            message = template.format(deviceID, 'subscribe')
            gatewayState.subscriptions[subscribe_topic] = clientAddr

            udpSerSock.sendto(message.encode('utf8'), clientAddr)

        else:
            print('undefined action: {}'.format(action))

    print('Finished.')

if __name__ == '__main__':
    main()