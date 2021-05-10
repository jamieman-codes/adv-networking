import socket
import sys
from sense_hat import SenseHat
from common import RunAction

#Constants
COLOURS = {"WHITE": (255,255,255),
            "RED": (255, 0 ,0),
            "BLUE" : (0, 0, 255),
            "GREEN" : (0, 255, 0),
            "PURPLE": (153, 0, 153),
            "YELLOW": (255, 255, 0),
            "TURQUOISE": (0, 255, 255),
            "ORANGE": (255, 128, 0),
            "PINK": (255, 102, 255),
            "BROWN": (51, 25, 0),
            "BLACK": (0,0,0)}

ADDR = '192.168.0.99'
PORT = 10000
DEVICE_ID = "led-matrix"

print('Starting device {}'.format(DEVICE_ID))
# Create a UDP socket
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (ADDR, PORT)

sense = SenseHat()

try:
    #Attach to gateway, let cloud IoT know device is online, then subscribe to messages. 
    RunAction('attach', DEVICE_ID, client_sock, server_address)
    RunAction('event',  DEVICE_ID, client_sock, server_address,'LED is online')
    RunAction('subscribe',  DEVICE_ID, client_sock, server_address)

    while True:
        #Get response
        response = client_sock.recv(4096).decode('utf8')
        print('Client received {}'.format(response))
        #Process response
        responseSplit = response.split(" ")
        if responseSplit[0] == "ON":
            if responseSplit[1] == "MATRIX":
                resMatrix = responseSplit[2].split(",")
                matrix = []
                for colour in resMatrix:
                    matrix.append(COLOURS[colour])
                sense.set_pixels(matrix)
                print("LED Matrix showing custom matrix")
            elif responseSplit[1] in COLOURS.keys():
                sense.clear(COLOURS[responseSplit[1]])
                print("LED Matrix showing: {}".format(responseSplit[1]))
            else:
                print('Invalid message {}'.format(response))
        elif responseSplit[0] == "OFF":
            sense.clear(COLOURS["BLACK"])
            print("LED Matrix OFF")
        else:
            print('Invalid message {}'.format(response))

finally:
    RunAction('event',  DEVICE_ID, client_sock, server_address,'LED is offline')
    print('closing socket', file=sys.stderr)
    client_sock.close()
