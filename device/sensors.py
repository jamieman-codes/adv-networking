import sys
import socket
import time
from sense_hat import SenseHat
from common import RunAction

sense = SenseHat()

ADDR = '192.168.0.99'
PORT = 10000
DEVICE_ID = "sensors"

print('Starting device {}'.format(DEVICE_ID))

# Create a UDP socket
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (ADDR, PORT)

try:
    RunAction('attach', DEVICE_ID, client_sock, server_address)
    RunAction('event', DEVICE_ID, client_sock, server_address, 'Sensor is online')

    while True:
        h = "{:.3f}".format(sense.get_humidity())
        t = "{:.3f}".format(sense.get_temperature())
        p = "{:.3f}".format(sense.get_pressure())

        print('Temp: {}, Hum: {}, Pressure: {}'.format(t, h, p))
        RunAction('event', DEVICE_ID, client_sock, server_address,'temperature={}, humidity={}, pressure={}'.format(t, h, p), False)

        time.sleep(2)


finally:
    RunAction('event', DEVICE_ID, client_sock, server_address,'LED is offline')
    print('closing socket', file=sys.stderr)
    client_sock.close()
