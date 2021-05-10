def SendCommand(sock, message, server_address):
    sock.sendto(message.encode(), server_address)
    response = sock.recv(4096)
    return response

def MakeMessage(action, device_id, data=''):
    if data:
        return '{{ "device" : "{}", "action":"{}", "data" : "{}" }}'.format(
            device_id, action, data)
    else:
        return '{{ "device" : "{}", "action":"{}" }}'.format(device_id, action)

def RunAction(action, device_id, client_sock, server_address, data='', log = True):
    message = MakeMessage(action, device_id, data)
    if not message:
        return
    if log:
        print('Send data: {} '.format(message))
    event_response = SendCommand(client_sock, message, server_address)
    if log:
        print('Response {}'.format(event_response))