# contains basic routines

import webrepl
import network
import uasyncio as asyncio
import urandom

from config import netcfg
from device import device_instance

from lib.umqttsimple import MQTTClient, MQTTException

# network routines


async def wifi_init():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    # station.config(dhcp_hostname=netcfg.hostname)
    station.connect(netcfg.wlan_ssid, netcfg.wlan_password)
    while not station.isconnected():
        await show_no_wifi()
    print('Connection successful')
    print(station.ifconfig())
    if netcfg.webrepl_enabled:
        webrepl.start()


async def mqtt_init(callback):
    station = network.WLAN(network.STA_IF)
    if not station.isconnected():
        await wifi_init()
    
    _ip = str(station.ifconfig()[0]).split('.')
    broker_ip = '.'.join(_ip[:3] + ['4'])
    cfg = netcfg.mqtt

    netcfg.mqtt_conn = False

    client = MQTTClient(
        netcfg.mqtt.get('client_id'),
        broker_ip,
        port=cfg['port'],
        user=cfg['user'],
        password=cfg['password'],
        keepalive=netcfg.keepalive
    )
    client.set_callback(callback)  # awful
    netcfg.client = client

    while not netcfg.mqtt_conn:
        client.connect()
        await show_no_broker()
        try:
            subscribe_to = netcfg.sub_topics
            for topic in subscribe_to:
                client.subscribe(topic)
            cmd_out = '{"timestamp":1}'
            client.publish(netcfg.topics['pub'], cmd_out)
            netcfg.mqtt_conn = True
        except MQTTException:
            pass

    print(f'connected to {broker_ip}, subscribed to {subscribe_to}')
    await show_broker_connect()


async def send_pong():
    if netcfg.ping_msg != b'':
        netcfg.client.publish(netcfg.topics['pub_id_pong'], netcfg.ping_msg)
        netcfg.ping_msg = b''


# device routines


async def blink_led(led, count, interval=250):
    for x in range(count):
        led.on()
        await asyncio.sleep_ms(interval)
        led.off()
        await asyncio.sleep_ms(interval)


async def show_no_wifi():
    await blink_led(device_instance.pins['red'], 6, 500)


async def show_no_broker():
    await blink_led(device_instance.pins['blue'], 6)


async def show_wifi_connect():
    await blink_led(device_instance.pins['green'], 6)


async def show_broker_connect():
    await blink_led(device_instance.pins['green'], 3)


# helpers

def randint(_min, _max):
    span = int(_max) - int(_min) + 1
    div = 0x3fffffff // span
    offset = urandom.getrandbits(30) // div
    val = int(_min) + offset
    return val


def to_hex(slice):
    return int(int(slice, 16) * 4)


def time_phase(time_change):
    t = time_change.split('-')
    if len(t) < 2:
        return int(t[0])
    else:
        return randint(t[0], t[1])
