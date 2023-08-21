import machine
import uasyncio as asyncio


class Device:

    pins = {
        'red': machine.Pin(14, machine.Pin.OUT),
        'green': machine.Pin(12, machine.Pin.OUT),
        'blue': machine.Pin(27, machine.Pin.OUT),
        'STR': machine.Pin(25, machine.Pin.OUT),
        'LGT': machine.Pin(26, machine.Pin.OUT)
    }

    colors = {
        'red': 0.75,
        'green': 0.95,
        'blue': 1.0
    }

    device = {
        'redK': 0.75,
        'greenK': 0.95,
        'blueK': 1.0,
    }

    quant_num = 50
    _pwm = {}
    _sequence = {}

    @staticmethod
    def _peripheral():
        return {
            'len': 0,
            'mode': '',
            'onoff': [],
            'time_static': [],
            'time_current': 0,
            'time_slice': 0,
            'count': 0,
            'last': 0,
            'current_command': []
        }

    def pwm_init(self):
        try:
            [self._pwm[col].duty(int(self._sequence['RGB'][col] * self.colors[col])) for col in self._pwm]
        except:  # noqa
            print('cannot set PWM, check config:\n{}'.format(self._pwm))

    @property
    def pwm(self):
        if not self._pwm:
            self._pwm = {p: machine.PWM(self.pins[p], freq=1000) for p in self.pins if p in ('red', 'green', 'blue')}
        return self._pwm

    @property
    def sequence(self):
        if not self._sequence:
            self._sequence = self._get_sequence()
        return self._sequence

    @sequence.setter
    def sequence(self, new_sequence):
        self._sequence = new_sequence

    def _get_sequence(self):
        sequence = dict()
        sequence['LGT'] = self._peripheral()
        sequence['STR'] = self._peripheral()
        sequence['RGB'] = self._peripheral()

        sequence['RGB'].update({
            'color': [],
            'red': 0,
            'green': 0,
            'blue': 0,
            'delta': {'red': 0, 'green': 0, 'blue': 0},
            'time_change': [],
            'quant': {'num': self.quant_num, 'count': 0, 'flag': 0},
        })

        return sequence

    def reset(self):
        self.pins['STR'].value(0)
        self.pins['LGT'].value(0)
        try:
            for color in self._pwm:
                self._pwm[color].duty(0)
        except Exception:  # noqa
            print(f'cannot set PWM, check config:\n{self._pwm}')
    
    def manage_rgb(payload, chan_name):
        if len(payload) < 4 or (len(payload)-1)%3 != 0:
            return
        commands = set(payload) & set(self.sequence[chan_name]['current_command'])
        if len(payload) == len(commands):
            print("Already executed")
            return
        self.sequence[chan_name]['current_command'] = payload 
        self.sequence[chan_name].update({
            'mode': payload[-1],  
            'len': int((len(payload)-1)/3),  
            'color': [],
            'time_static': [],
            'time_change': [],
            'count': 0,
            'time_current': time.ticks_ms(),
        })
        for i in range(self.sequence[chan_name]['len']):
            self.sequence[chan_name]['color'].append(payload[i * 3])
            self.sequence[chan_name]['time_static'].append(payload[i * 3 + 1])
            self.sequence[chan_name]['time_change'].append(payload[i * 3 + 2])
        self.sequence[chan_name]['time_slice'] = time_phase(self.sequence[chan_name]['time_static'][0])
        self.sequence[chan_name]['time_current'] = time.ticks_ms()
        self.sequence[chan_name]['quant']['count'] = 0
        self.sequence[chan_name]['quant']['flag'] = 0
        self.manage_pwm(0)

    def manage_discr(payload, chan_name):
        if len(payload) < 3 or (len(payload)-1)%2 != 0:
            return
        commands = set(payload) & set(self.sequence[chan_name]['current_command'])
        if len(payload) == len(commands):
            print("Already executed")
            return
        self.sequence[chan_name]['current_command'] = payload 
        self.sequence[chan_name].update({
            'mode': payload[-1],  
            'len': int((len(payload)-1)/2),
            'onoff': [],
            'time_static': [],
            'count': 0,
        })
        self.sequence[chan_name]['time_change'] = []
        for i in range(self.sequence[chan_name]['len']):
            self.sequence[chan_name]['onoff'].append(payload[i * 2])
            self.sequence[chan_name]['time_static'].append(payload[i * 2 + 1])
        self.pins[chan_name].value(int(self.sequence[chan_name]['onoff'][self.sequence[chan_name]['count']]))
        self.sequence[chan_name]['time_slice'] = time_phase(str(self.sequence[chan_name]['time_static'][0]))


    def exec_discr(chan_name):
        if (time.ticks_ms() - self.sequence[chan_name]['time_current']) >= self.sequence[chan_name]['time_slice']:
            if self.sequence[chan_name]['mode'] == 'C':
                self.sequence[chan_name]['count'] = (self.sequence[chan_name]['count'] + 1) % self.sequence[chan_name]['len']
            elif self.sequence[chan_name]['mode'] == 'S':
                self.sequence[chan_name]['count'] += 1
                if self.sequence[chan_name]['count'] >= self.sequence[chan_name]['len']:
                    self.sequence[chan_name]['len'] = 0
                    self.sequence[chan_name]['current_command'] = []
                    return
            self.sequence[chan_name]['time_slice'] = time_phase(self.sequence[chan_name]['time_static'][self.sequence[chan_name]['count']])
            self.pins[chan_name].value(int(self.sequence[chan_name]['onoff'][self.sequence[chan_name]['count']]))
            self.sequence[chan_name]['time_current'] = time.ticks_ms()
    
    def manage_pwm_delta(prev_idx):
        rgb_seq = self.sequence['RGB']
        quant = rgb_seq['quant']

        if quant['flag'] == 0:
            idx = rgb_seq['count']
            color_now = rgb_seq['color'][idx]
            color_prev = rgb_seq['color'][prev_idx]

            delta_red = int((utils.to_hex(color_now[:2]) - utils.to_hex(color_prev[:2])) / quant['num'])
            delta_green = int((utils.to_hex(color_now[2:4]) - utils.to_hex(color_prev[2:4])) / quant['num'])
            delta_blue = int((utils.to_hex(color_now[4:6]) - utils.to_hex(color_prev[4:6])) / quant['num'])

            rgb_seq['delta']['red'] = delta_red
            rgb_seq['delta']['green'] = delta_green
            rgb_seq['delta']['blue'] = delta_blue

            quant['flag'] = 1

        quant['count'] += 1

        for key in rgb_seq['delta']:
            rgb_seq[key] += rgb_seq['delta'][key]
        self.init_pwm()

    def manage_pwm(idx):
        _color = self.sequence['RGB']['color']
        self.sequence['RGB']['red'] = utils.to_hex(_color[idx][:2])
        self.sequence['RGB']['green'] = utils.to_hex(_color[idx][2:4])
        self.sequence['RGB']['blue'] = utils.to_hex(_color[idx][4:6])
        self.init_pwm()
    
    async def run():
        if self.sequence['RGB'].get('len') > 0:
            if (time.ticks_ms() - self.sequence['RGB']['time_current']) >= self.sequence['RGB']['time_slice']:
                before = self.sequence['RGB']['count']
                self.sequence['RGB']['time_current'] = time.ticks_ms()
                if self.sequence['RGB']['quant']['flag'] == 0:
                    if self.sequence['RGB']['mode'] == 'C':
                        self.sequence['RGB']['count'] = (before + 1) % self.sequence['RGB']['len']
                    elif self.sequence['RGB']['mode'] == 'S':
                        self.sequence['RGB']['count'] += 1
                        if self.sequence['RGB']['count'] >= self.sequence['RGB']['len']:
                            self.sequence['RGB']['len'] = 0
                            continue
                    try:
                        tc = int(self.sequence['RGB'].get('time_change')[before])
                        if tc > 0:
                            self.sequence['RGB']['time_slice'] = int(tc/self.sequence['RGB']['quant']['num'])
                            self.manage_pwm_delta(before)
                        else:
                            self.sequence['RGB']['time_slice'] = time_phase(self.sequence['RGB']['time_static'][self.sequence['RGB']['count']])
                            self.manage_pwm(self.sequence['RGB']['count'])
                    except IndexError:
                        print('index error in RGB conf')
                elif self.sequence['RGB']['quant']['flag'] == 1:
                    self.manage_pwm_delta(before)
                    if self.sequence['RGB']['quant']['count'] >= self.sequence['RGB']['quant']['num']:
                        self.sequence['RGB']['quant']['count'] = 0
                        self.sequence['RGB']['quant']['flag'] = 0
                        self.sequence['RGB']['time_slice'] = time_phase(self.sequence['RGB']['time_static'][self.sequence['RGB']['count']])
                        continue
        if self.sequence['STR'].get('len') > 0:
            self.exec_discr('STR')
        if self.sequence['LGT'].get('len') > 0:
            self.exec_discr('LGT')
        await asyncio.sleep_ms(10)

    def handle(self, new_command, *args, **kwargs):
        for cmd, val in self.sequence.items():
            data = new_command.get(cmd) 
            if not data:
                continue
            if data != val.get('current_command'):
                payload = data.split('/')
                if payload[0] == 'RESET':
                    machine.reset()
                else:
                    if cmd == 'RGB':
                        self.manage_rgb(payload, cmd)
                    else:
                        self.manage_discr(payload, cmd)
 
device_instance = Device()
