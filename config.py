# contains network and device configurations

import machine

from network import WLAN
from ubinascii import hexlify

CLIENT_TYPE = 'rgb'

# device constants

CLIENT_ID = hexlify(machine.unique_id())
CLIENT_MAC = hexlify(WLAN().config('mac'))


class NetworkConfig:

    hostname = f'Boiler-{CLIENT_ID}'.encode()

    wlan_ssid = 'ArmyDep'
    wlan_password = 'z0BcfpHu'

    keepalive = 30

    mqtt = {
        'port': 1883,
        'user': b'mqtt',
        'password': b'skabent0mqtt',
        'last_message': 0,
        'message_interval': 5,
        'counter': 0,
    }

    topics = {
        'sub': f'{CLIENT_TYPE}/all/cup'.encode(),
        'sub_id': f'{CLIENT_TYPE}/{CLIENT_MAC}/cup'.encode(),
        'sub_ping': f'{CLIENT_TYPE}/all/ping'.encode(),
        'pub': f'ask/{CLIENT_TYPE}/all/cup'.encode(),
        'pub_id_pong': f'ask/{CLIENT_TYPE}/{CLIENT_MAC}/pong'.encode(),
    }

    ping_msg = b''
    mqtt_conn = False

    @property
    def sub_topics(self):
        return [self.topics[t] for t in self.topics if 'sub' in t]


netcfg = NetworkConfig()
