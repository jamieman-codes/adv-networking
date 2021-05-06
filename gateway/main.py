

# [START iot_mqtt_run]
def main():
    global gateway_state
    global skip_next_sub

    args = parse_command_line_args()

    gateway_state.mqtt_config_topic = '/devices/{}/config'.format(
            parse_command_line_args().gateway_id)
    gateway_state.mqtt_error_topic = '/devices/{}/errors'.format(
            parse_command_line_args().gateway_id)

    gateway_state.mqtt_bridge_hostname = args.mqtt_bridge_hostname
    gateway_state.mqtt_bridge_port = args.mqtt_bridge_hostname

    client = get_client(
        args.project_id, args.cloud_region, args.registry_id, args.gateway_id,
        args.private_key_file, args.algorithm, args.ca_certs,
        args.mqtt_bridge_hostname, args.mqtt_bridge_port,
        args.jwt_expires_minutes)

    while True:
        client.loop()
        if gateway_state.connected is False:
            print('connect status {}'.format(gateway_state.connected))
            time.sleep(1)
            continue

        try:
            data, client_addr = udpSerSock.recvfrom(BUFSIZE)
        except socket.error:
            continue
        print('[{}]: From Address {}:{} receive data: {}'.format(
                ctime(), client_addr[0], client_addr[1], data.decode("utf-8")))

        command = json.loads(data.decode('utf-8'))
        if not command:
            print('invalid json command {}'.format(data))
            continue

        action = command["action"]
        device_id = command["device"]
        template = '{{ "device": "{}", "command": "{}", "status" : "ok" }}'

        if action == 'event':
            print('Sending telemetry event for device {}'.format(device_id))
            payload = command["data"]

            mqtt_topic = '/devices/{}/events'.format(device_id)
            print('Publishing message to topic {} with payload \'{}\''.format(
                    mqtt_topic, payload))
            _, event_mid = client.publish(mqtt_topic, payload, qos=0)

            message = template.format(device_id, 'event')
            udpSerSock.sendto(message.encode('utf8'), client_addr)

        elif action == 'attach':
            print('Sending telemetry event for device {}'.format(device_id))
            attach_topic = '/devices/{}/attach'.format(device_id)
            auth = ''  # TODO:    auth = command["jwt"]
            attach_payload = '{{"authorization" : "{}"}}'.format(auth)

            print('Attaching device {}'.format(device_id))
            print(attach_topic)
            response, attach_mid = client.publish(
                    attach_topic, attach_payload, qos=1)

            message = template.format(device_id, 'attach')
            udpSerSock.sendto(message.encode('utf8'), client_addr)
        elif action == 'detach':
            detach_topic = '/devices/{}/detach'.format(device_id)
            print(detach_topic)

            res, mid = client.publish(detach_topic, "{}", qos=1)

            message = template.format(res, mid)
            print('sending data over UDP {} {}'.format(client_addr, message))
            udpSerSock.sendto(message.encode('utf8'), client_addr)

        elif action == "subscribe":
            print('subscribe config for {}'.format(device_id))
            subscribe_topic = '/devices/{}/config'.format(device_id)
            skip_next_sub = True

            _, mid = client.subscribe(subscribe_topic, qos=1)
            message = template.format(device_id, 'subscribe')
            gateway_state.subscriptions[subscribe_topic] = client_addr

            udpSerSock.sendto(message.encode('utf8'), client_addr)

        else:
            print('undefined action: {}'.format(action))

    print('Finished.')

if __name__ == '__main__':
    main()