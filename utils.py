# contains basic routines

import time
import webrepl
import uasyncio as asyncio
import urandom

from utime import ticks_diff, ticks_ms

from config import netcfg
from device import device_instance

# network routines


async def wifi_init(station):
    station.active(True)
    station.config(dhcp_hostname=netcfg.hostname)
    station.connect(netcfg.wlan_ssid, netcfg.wlan_password)
    while not station.isconnected():
        show_no_wifi()
        asyncio.sleep_ms(100)
    print('Connection successful')
    print(station.ifconfig())
    webrepl.start()


async def heartbeat(station, client):
    while True:
        if not station.isconnected():
            await wifi_init(station)
        if ticks_diff(ticks_ms(), client.last_ping) > netcfg.keepalive * 1000:
            netcfg.mqtt_conn = False
        asyncio.sleep_ms(1000)


def send_pong(msg, client):
    if netcfg.msg != b'':
        client.publish(netcfg.topics['pub_id_pong'], msg)
        netcfg.msg = b''


# device routines


def blink_led(led, count, interval=0.25):
    for x in range(count):
        led.duty(1023)
        time.sleep(interval)
        led.duty(0)
        time.sleep(interval)


def show_no_wifi():
    blink_led(device_instance.pins['red'], 6, 0.5)


def show_no_broker(led):
    blink_led(device_instance.pins['blue'], 6)


def show_wifi_connect(pwm):
    blink_led(device_instance.pins['green'], 6)


def show_broker_connect(pwm):
    blink_led(device_instance.pins['green'], 3)


# helpers

def randint(_min, _max):
    span = int(_max) - int(_min) + 1
    div = 0x3fffffff // span
    offset = urandom.getrandbits(30) // div
    val = int(_min) + offset
    return val


def _hex(slice):
    return int(int(slice, 16) * 4)


def time_phase(time_change):
    t = time_change.split('-')
    if len(t) < 2:
        return int(t[0])
    else:
        return randint(t[0], t[1])
