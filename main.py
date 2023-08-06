# contains main flow description

import ujson
import network
import uasyncio as asyncio

import umqttsimple

from config import netcfg
from device import device_instance
from utils import wifi_init, send_pong, heartbeat

STATION = network.WLAN(network.STA_IF)
current_task = None


def mqtt_callback(topic, msg):
    global current_task

    if topic == netcfg.topics['sub_ping']:
        netcfg.ping_msg = msg
        return

    if topic not in (netcfg.topics['sub'], netcfg.topics['sub_id']):
        return

    if current_task is not None:
        current_task.cancel()

    async def _handler():
        try:
            cmd = ujson.loads(msg)
            datahold = cmd.get('datahold')
            device_instance.handle(datahold)
        except Exception:  # noqa
            asyncio.sleep_ms(200)

    current_task = asyncio.create_task(_handler)


def connect_and_subscribe(station):
    _ip = str(station.ifconfig()[0]).split('.')
    broker_ip = '.'.join(_ip[:3] + ['254'])
    cfg = netcfg.mqtt

    client = umqttsimple.MQTTClient(netcfg.mqtt.get('client_id'),
                                    broker_ip,
                                    port=cfg['port'],
                                    user=cfg['user'],
                                    password=cfg['password'],
                                    keepalive=cfg['keepalive'])

    client.set_callback(mqtt_callback)

    try:
        client.connect()
    except Exception:  # noqa
        netcfg.mqtt_conn = False
        return client

    subscribe_to = netcfg.sub_topics
    for topic in subscribe_to:
        client.subscribe(topic)
    print(f'connected to {broker_ip}, subscribed to {subscribe_to}')

    try:
        cmd_out = '{"timestamp":1}'
        client.publish(netcfg.topics['pub'], cmd_out)
        netcfg.mqtt_conn = True
    except Exception:  # noqa
        netcfg.mqtt_conn = False
    device_instance.reset()
    return client


async def connect_and_listen(station, client):
    while True:
        if not netcfg.mqtt_conn:
            client = connect_and_subscribe(station)
            asyncio.sleep(100)
            continue

        try:
            client.check_msg()
            asyncio.sleep_ms(100)
        except OSError:  # noqa
            netcfg.mqtt_conn = False
            continue

        if netcfg.ping_msg != b'':
            send_pong(netcfg.ping_msg, client)
            netcfg.ping_msg = b''


async def main():
    device_instance.reset()
    await wifi_init(STATION)
    client = connect_and_subscribe(STATION)
    asyncio.create_task(heartbeat(STATION, client))
    asyncio.create_task(connect_and_listen(STATION, client))


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
