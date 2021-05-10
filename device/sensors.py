import random
import sys
import socket
import time

from sense_hat import SenseHat

sense = SenseHat()

DHT_SENSOR_PIN = 4

ADDR = '192.168.0.99'
PORT = 10000
# Create a UDP socket
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (ADDR, PORT)
DEVICE_ID = "sensors"

print('Bringing up device {}'.format(DEVICE_ID))


def SendCommand(sock, message, log=True):
    """ returns message received """
    if log:
        print('sending: "{}"'.format(message), file=sys.stderr)

    sock.sendto(message.encode('utf8'), server_address)

    # Receive response
    if log:
        print('waiting for response', file=sys.stderr)

    response, _ = sock.recvfrom(4096)

    if log:
        print('received: "{}"'.format(response), file=sys.stderr)

    return response


print('Bring up device 1')


def MakeMessage(action, data=''):
    if data:
        return '{{ "device" : "{}", "action":"{}", "data" : "{}" }}'.format(
            DEVICE_ID, action, data)
    else:
        return '{{ "device" : "{}", "action":"{}" }}'.format(DEVICE_ID, action)


def RunAction(action):
    message = MakeMessage(action)
    if not message:
        return
    print('Send data: {} '.format(message))
    event_response = SendCommand(client_sock, message)
    print('Response {}'.format(event_response))


try:
    RunAction('attach')

    while True:
        temp = sense.get_temperature()
        hue = sense.get_humidity()
        pressure = sense.get_pressure()

        h = "{:.3f}".format(hue)
        t = "{:.3f}".format(temp)
        p = "{:.3f}".format(pressure)
        print('Temp: {}, Hum: {}, Pressure: {}'.format(t, h, p))
        message = MakeMessage('event', 'temperature={}, humidity={}, pressure={}'.format(t, h, p))

        SendCommand(client_sock, message, False)
        time.sleep(2)


finally:
    print('closing socket', file=sys.stderr)
    client_sock.close()
