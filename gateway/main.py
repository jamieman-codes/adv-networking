import paho.mqtt.client as mqtt
import ssl
import datetime
import jwt
import socket

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

class State:
    mqtt_config_topic = '/devices/{}/config'.format(GATEWAY_ID) # This is the topic that the device will receive configuration updates on.
    mqtt_error_topic = '/devices/{}/errors'.format(GATEWAY_ID)  # This is the topic that the device will receive configuration updates on.

    mqtt_bridge_hostname = MQTT_BRIDGE_HOST
    mqtt_bridge_port = MQTT_BRIDGE_PORT

    pending_responses = {} # for all PUBLISH messages which are waiting for PUBACK. The key is 'mid'

    pending_subscribes = {} # SUBSCRIBE messages waiting for SUBACK. The key is 'mid' from Paho.
 
    subscriptions = {} # for all SUBSCRIPTIONS. The key is subscription topic.

    connected = False # Indicates if MQTT client is connected or not

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

def on_disconnect(client, unused_userdata, rc):

def on_publish(unused_client, userdata, mid):

def on_subscribe(unused_client, unused_userdata, mid, granted_qos):

def on_message(unused_client, unused_userdata, message):

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
    #Create MQTT Client
    gatewayState = State()
    client = create_client()

    #Create UDP socket
    udpSerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSerSock.setblocking(False)
    udpSerSock.bind(ADDR)
    
    #Main loop
    while True:
    

if __name__ == '__main__':
    main()