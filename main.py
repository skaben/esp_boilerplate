# contains main flow description

import ujson
import network
import uasyncio as asyncio
import utils

from lib import umqttsimple
from utime import ticks_diff, ticks_ms

from config import netcfg
from device import device_instance

loop = asyncio.get_event_loop()
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

    async def msg_handler(message):
        try:
            cmd = ujson.loads(message)
            datahold = cmd.get('datahold')
            device_instance.handle(datahold)
        except Exception:  # noqa
            await asyncio.sleep_ms(200)

    current_task = asyncio.create_task(msg_handler(msg))


async def routine():
    device_instance.reset()
    station = network.WLAN(network.STA_IF)
    while True:
        if not station.isconnected():
            await utils.wifi_init()
        if not netcfg.client or not netcfg.mqtt_conn:
            await utils.mqtt_init(mqtt_callback)

        last_ping = netcfg.client.last_ping or 0
        if ticks_diff(ticks_ms(), last_ping) > netcfg.keepalive * 1000:
            netcfg.mqtt_conn = False

        if netcfg.mqtt_conn:
            try:
                netcfg.client.check_msg()
                await utils.send_pong()
                await device_instance.run()
                await asyncio.sleep_ms(100)
            except OSError:  # noqa
                netcfg.mqtt_conn = False
                continue
        

async def main():
    await utils.wifi_init()
    await utils.mqtt_init(mqtt_callback)
    device_instance.reset()
    asyncio.create_task(routine())


loop.create_task(main())
loop.run_forever()
