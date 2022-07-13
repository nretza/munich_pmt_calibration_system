#!/usr/bin/python3
from omcu.devices.device import serial_device

class Laser(serial_device):
    """
    This is a class for the Picosecond Laser System Controller EIG2000DX
    
    This is a Singleton - google it!
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = Laser()
        return cls._instance

    def __init__(self, dev="/dev/Laser_control", simulating=False, delay=.1):

        if Laser._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            Laser._instance = self

        super().__init__(dev=dev, simulating=simulating, delay=delay)

        self.off_pulsed()  # pulsed laser emission OFF
        self.set_trig_edge(1)  # trigger edge: rising
        self.set_trig_source(0)  # trigger source: internal
        self.set_trig_level(0)  # trigger level: 0 mV
        self.set_tune_value(710)  # tune value at 71%
        self.set_freq(10e3)  # frequency = 10 kHZ
        self.off_cw()  # CW laser emission OFF


    def print_state(self):  #TODO: prints not whole information
        """
        This function prints system state information in the format:
        --------------------
        interlock:			disabled
        laser emission:		off
        CW emission:		off
        trigger source:		internal
        trigger edge:		rising
        tune mode:			auto
        tune value: 	     71.00 %
        laser head temp.:      25.43 C
        int. frequency:	      1000 Hz
        ext. frequency:	         0 Hz
        trigger level:	     +0.00 V
        """
        s = self.serial_io('state?', multi_line=True)
        print(s)

    def on_pulsed(self):
        """
        This function enables the pulsed laser emission (laser on)
        :return: int: 0 = emission off, 1 = emission on, (2 = something went wrong)
        """
        self.serial_io('ld=1')  # enables pulsed laser emission
        return self.get_ld()

    def off_pulsed(self):
        """
        This function disables the pulsed laser emission (laser off)
        :return: int: 0 = emission off, 1 = emission on, (2 = something went wrong)
        """
        self.serial_io('ld=0')  # disables pulsed laser emission
        return self.get_ld()

    def get_ld(self):
        """
        This is a function to get information about the pulsed laser emission state
        :return: int: 0 = emission off, 1 = emission on, (2 = something went wrong)
        """
        ld_string = self.serial_io('ld?')  # returns string 'pulsed laser emission: off/on'
        print(ld_string)
        if 'off' in ld_string:
            ld_val = 0
        elif ' on' in ld_string:
            ld_val = 1
        elif 'test' in ld_string:
            ld_val = 0
        else:
            ld_val = 2
            print('Error: pulsed laser emission state could not be determined. Try again!')
        return ld_val

    def set_trig_edge(self, te):
        """
        This is a function to set the trigger edge
        :param te: trigger edge (falling 0, rising 1)
        :return: int: 0 = falling, 1 = rising, (2 = something went wrong)
        """
        self.serial_io(f'te={te}', line_ending=b'\n')  # sets trigger edge to te (falling 0, rising 1)
        return self.get_trig_edge()

    def get_trig_edge(self):
        """
        This is a function to get information about the set trigger edge
        :return: int: 0 = falling, 1 = rising, (2 = something went wrong)
        """
        te_string = self.serial_io('te?')  # returns string 'trigger edge: falling/rising'
        print(te_string)
        if 'falling' in te_string:
            te_val = 0
        elif 'rising' in te_string:
            te_val = 1
        elif 'test' in te_string:
            te_val = 0
        else:
            te_val = 2
            print('Error: trigger edge could not be determined. Try again!')
        return te_val

    def set_trig_source(self, ts):
        """
        This is a function to set the trigger source
        :param ts: trigger source (internal 0, ext. adjustable 1, ext. TTL 2)
        :return: int: 0 = internal, 1 = ext. adjustable, 2 = ext. TTL, (3 = something went wrong)
        """
        self.serial_io(f'ts={ts}', line_ending=b'\n')  # sets trigger source to ts
        # (internal 0, ext. adj. 1, ext. TTL 2)
        return self.get_trig_source()

    def get_trig_source(self):
        """
        This is a function to get information about the set trigger source
        :return: int: 0 = internal, 1 = ext. adjustable, 2 = ext. TTL, (3 = something went wrong)
        """
        ts_string = self.serial_io('ts?')  # returns string 'trigger source: internal/ext. adjustable/ext. TTL'
        print(ts_string)
        if 'internal' in ts_string:
            ts_val = 0
        elif 'adjustable' in ts_string:
            ts_val = 1
        elif 'TTL' in ts_string:
            ts_val = 2
        elif 'test' in ts_string:
            ts_val = 0
        else:
            ts_val = 3
            print('Error: trigger source could not be determined. Try again!')
        return ts_val

    def set_trig_level(self, tl):
        """
        This is a function to set the trigger level
        :param tl: trigger level (-4800...+4800 mV)
        :return: float: trigger level (-4.80...+4.80 V)
        """
        self.serial_io(f'tl={tl}', line_ending=b'\n')  # sets trigger level to tl (-4800...+4800 mV)
        return self.get_trig_level()

    def get_trig_level(self):
        """
        This is a function to get information about the set trigger level
        :return: float: trigger level (-4.80...+4.80 V)
        """
        tl_string = self.serial_io('tl?')  # returns string 'trigger level: +0.00 V'
        print(tl_string)
        if 'test' in tl_string:
            tl_val = 0
        else:
            tl_val = float(tl_string[16:25])  # makes float from string of trigger level value
        return tl_val

    def set_tune_mode(self, tm):
        """
        This is a function to set the tune mode
        :param tm: tune mode (manual 0, auto 1)
        :return: int: 0 = manual, 1 = auto, (2 = something went wrong)
        """
        self.serial_io(f'tm={tm}', line_ending=b'\n')  # sets tune mode to tm (manual 0, auto 1)
        return self.get_tune_mode()

    def get_tune_mode(self):
        """
        This is a function to get information about the set tune mode
        :return: int: 0 = manual, 1 = auto, (2 = something went wrong)
        """
        tm_string = self.serial_io('tm?')  # returns string 'tune mode: manual/auto'
        print(tm_string)
        if 'auto' in tm_string:
            tm_val = 1
        elif 'manual' in tm_string:
            tm_val = 0
        elif 'test' in tm_string:
            tm_val = 3
        else:
            tm_val = 2
            print('Error: tune mode could not be determined. Try again!')
        return tm_val

    def set_tune_value(self, tune):
        """
        This is a function to set a tune value
        It sets first the tune mode to manual
        :param tune: tune value (0...1000, where 1000=100 %)
        :return: float: tune value (0...100.0 %)
        """
        self.serial_io('tm=0')  # sets tune mode to manual
        tune_mode_0 = self.get_tune_mode()
        print(tune_mode_0)
        self.serial_io(f'tune={tune}', line_ending=b'\n')  # sets tune value to tune (0...1000, where 1000=100 %)
        return self.get_tune_value()

    def get_tune_value(self):
        """
        This is a function to get information about the set tune value
        :return: float: tune value (0...100.0 %)
        """
        tune_string = self.serial_io('tune?')  # returns string 'tune value: 70.00 %'
        print(tune_string)
        if 'test' in tune_string:
            tune_val = 0
        else:
            tune_val = float(tune_string[15:24])  # makes float from string of tune level value
        return tune_val

    def set_freq(self, f):
        """
        This is a function to set the internal oscillator frequency
        :param f: frequency (25...125000000 Hz)
        :return: str: 'int. frequency: 100 Hz'
        """
        self.serial_io(f'f={f}', line_ending=b'\n')  # sets frequency to f (25...125000000)
        return self.get_freq()

    def get_freq(self):
        """
        This is a function to get information about the set frequency
        :return: float: frequency (25...125000000 Hz)
        """
        freq_string = self.serial_io('f?')  # returns string 'int. frequency: 100 Hz'
        print(freq_string)
        if 'test' in freq_string:
            freq = 0
        else:
            freq = float(freq_string[17:27])  # makes float from string of frequency value
        return freq

    def set_cwl(self, cwl):
        """
        This is a function to set the CW laser output power value
        :param cwl: CW laser output power (0...100 %)
        :return: float: CW laser output power (0...100 %)
        """
        self.serial_io(f'cwl={cwl}', line_ending=b'\n')  # sets CW laser output power (0...100)
        return self.get_cwl()

    def get_cwl(self):
        """
        This is a function to get information about the CW laser output power value
        :return: float: CW laser output power (0...100 %)
        """
        cwl_string = self.serial_io('cwl?')  # returns string 'CW output power: 0 %'
        print(cwl_string)
        if 'test' in cwl_string:
            cwl_val = 0
        else:
            cwl_val = float(cwl_string[16:19])  # makes float from string of frequency value
        return cwl_val

    def on_cw(self):
        """
        This is a function to enable the CW laser emission
        :return: int: 1 = on, (2 = something went wrong)
        """
        self.serial_io('cw=1')  # enables CW laser emission
        return self.get_cw()

    def off_cw(self):
        """
        This is a function to disable the CW laser emission
        :return: int: 0 = off, (2 = something went wrong)
        """
        self.serial_io('cw=0')  # disables CW laser emission
        return self.get_cw()

    def get_cw(self):
        """
        This is a function to get information about the CW laser emission state
        :return: int: 0 = off, 1 = on, (2 = something went wrong)
        """
        cw_string = self.serial_io('cw?')  # returns string 'CW laser emission: off/on'
        print(cw_string)
        if 'off' in cw_string:
            cw_val = 0
        elif ' on' in cw_string:
            cw_val = 1
        elif 'test' in cw_string:
            cw_val = 0
        else:
            cw_val = 2
            print('Error: CW laser emission state could not be determined. Try again!')
        return cw_val

    def get_temp(self):
        """
        This is a function to get the laser head temperature
        :return:
        """
        temp_str = self.serial_io('lht?')
        temp_float = float(temp_str[23:28])
        return temp_float

    def get_temp_ind(self):  #TODO: fix
        """
        This is a function to get information about the laser diode temperature indicator (good, bad)
        :return:
        """
        temp_ind = self.serial_io('ldtemp?')  #
        return temp_ind
