import machine


class Device:

    pins = {
        'red': machine.Pin(15, machine.Pin.OUT),
        'green': machine.Pin(13, machine.Pin.OUT),
        'blue': machine.Pin(12, machine.Pin.OUT),
        'STR': machine.Pin(14, machine.Pin.OUT),
        'LGT': machine.Pin(4, machine.Pin.OUT)
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
            self._sequence = self.get_sequence()
        return self._sequence

    def get_sequence(self):
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

    def handle(self, payload, *args, **kwargs):
        print(payload)


device_instance = Device()
