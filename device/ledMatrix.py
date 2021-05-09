import socket
import sys
from sense_hat import SenseHat

#Constants
WHITE = (255,255,255)
OFF = (0,0,0)
ADDR = '192.168.0.12'
PORT = 10000
DEVICE_ID = "led-matrix"
# Create a UDP socket
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (ADDR, PORT)

print('Starting device {}'.format(DEVICE_ID))

sense = SenseHat()

def SendCommand(sock, message):
    print('sending "{}"'.format(message))
    sock.sendto(message.encode(), server_address)

    # Receive response
    print('waiting for response')
    response = sock.recv(4096)
    print('received: "{}"'.format(response))

    return response


def MakeMessage( action, data=''):
    if data:
        return '{{ "device" : "{}", "action":"{}", "data" : "{}" }}'.format(
            DEVICE_ID, action, data)
    else:
        return '{{ "device" : "{}", "action":"{}" }}'.format(
            DEVICE_ID, action)


def RunAction(action, data=''):
    global client_sock
    message = MakeMessage(action, data)
    if not message:
        return
    print('Send data: {} '.format(message))
    event_response = SendCommand(client_sock, message)
    print('Response: {}'.format(event_response))


try:
    RunAction('detach')
    RunAction('attach')
    RunAction('event', 'LED is online')
    RunAction('subscribe')

    while True:
        response = client_sock.recv(4096).decode('utf8')
        print('Client received {}'.format(response))
        if response.upper() == 'ON' or response.upper() == b'ON':
            
            sense.clear(WHITE)
            print("LED Matrix showing: WHITE")
        elif response.upper() == "OFF" or response.upper() == b'OFF':
            
            sense.clear(OFF)
            print("LED Matrix OFF")
        else:
            print('Invalid message {}'.format(response))

finally:
    print('closing socket', file=sys.stderr)
    client_sock.close()
