#!/usr/bin/python3
import logging

import serial
import time
import numpy as np


class SimSerial:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f'Initialised with - args: {args}; kwargs: {kwargs}')

    @staticmethod  # function does not need self
    def readline():
        return_bytes = 'test str /n'
        return return_bytes.encode()

    @staticmethod
    def read():
        return f'{np.random.randint(0, 10)}'.encode()  # return one item

    @staticmethod
    def inWaiting():
        return np.random.random() < .8  # the probability is smaller to be False as True

    def write(self, bytes_str):
        self.logger.debug(f'SerialWrite: {bytes_str.decode().strip()}')  # .strip() to remove tailing '/n'


class Laser:
    """
    This is a class for the Picosecond Laser System Controller EIG2000DX
    """

    def __init__(self, dev="/dev/Laser_control", simulating=False, delay=.5):  # run sudo udevadm trigger before
        self.logger = logging.getLogger(type(self).__name__)

        # select if Serial or SimSerial
        if simulating:
            serial_connection = SimSerial
            self.delay = .01  # set default delay
        else:
            serial_connection = serial.Serial
            self.delay = delay  # set default delay

        # initialise Serial or SimSerial
        self.serial = serial_connection(dev,
                                        baudrate=19200,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout=2
                                        )

        self.off_pulsed()  # pulsed laser emission OFF
        self.set_trig_edge(1)  # trigger edge: rising
        self.set_trig_source(0)  # trigger source: internal
        self.set_trig_level(0)  # trigger level: 0 mV
        self.set_tune_mode(1)  # tune mode: auto
        self.set_freq(1000)  # frequency = 1 kHZ
        self.off_cw()  # CW laser emission OFF

    def __write_serial(self, cmd, delay=None, line_ending=b'\r\n'):  # "__" : private function for this class
        """

        PARAMETERS
        ----------
        cmd: Str, bytes, optional
        delay: float or None, optional
        line_ending: bytes, optional
        """
        if delay is None:
            delay = self.delay

        if type(cmd) is str:
            cmd = cmd.encode()

        if not cmd.endswith(line_ending):
            cmd += line_ending

        self.serial.write(cmd)
        time.sleep(delay)

        return_str = self.serial.readline().decode()

        self.logger.debug(f'Serial write cmd: {cmd}; return {return_str}')
        return return_str

    def print_state(self):
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
        self.__write_serial('state?')
        s = ''
        while self.serial.inWaiting():
            try:
                s += self.serial.read().decode()
            except:
                pass
        print(s)

    def on_pulsed(self):
        """
        This function enables the pulsed laser emission (laser on)
        :return: int: 0 = emission off, 1 = emission on, (2 = something went wrong)
        """
        self.__write_serial('ld=1')  # enables pulsed laser emission
        return self.get_ld()

    def off_pulsed(self):
        """
        This function disables the pulsed laser emission (laser off)
        :return: int: 0 = emission off, 1 = emission on, (2 = something went wrong)
        """
        self.__write_serial('ld=0')  # disables pulsed laser emission
        return self.get_ld()

    def get_ld(self):
        """
        This is a function to get information about the pulsed laser emission state
        :return: int: 0 = emission off, 1 = emission on, (2 = something went wrong)
        """
        ld_string = self.__write_serial('ld?')  # returns string 'pulsed laser emission: off/on'
        print(ld_string)
        if 'off' in ld_string[-3:]:
            ld_val = 0  # global variable is redefined
        elif 'on' in ld_string[-3:]:
            ld_val = 1  # global variable is redefined
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
        self.__write_serial(f'te={te}', line_ending=b'\n')  # sets trigger edge to te (falling 0, rising 1)
        return self.get_trig_edge()

    def get_trig_edge(self):
        """
        This is a function to get information about the set trigger edge
        :return: int: 0 = falling, 1 = rising, (2 = something went wrong)
        """
        te_string = self.__write_serial('te?')  # returns string 'trigger edge: falling/rising'
        print(te_string)
        te_val = 2  # global variable, place holder value
        if 'falling' in te_string[-7:]:
            te_val = 0  # variable is redefined as a local
        elif 'rising' in te_string[-7:]:
            te_val = 1  # variable is redefined as a local
        else:
            print('Error: trigger edge could not be determined. Try again!')
        return te_val

    def set_trig_source(self, ts):
        """
        This is a function to set the trigger source
        :param ts: trigger source (internal 0, ext. adjustable 1, ext. TTL 2)
        :return: int: 0 = internal, 1 = ext. adjustable, 2 = ext. TTL, (3 = something went wrong)
        """
        self.__write_serial(f'ts={ts}', line_ending=b'\n')  # sets trigger source to ts
        # (internal 0, ext. adj. 1, ext. TTL 2)
        return self.get_trig_source()

    def get_trig_source(self):
        """
        This is a function to get information about the set trigger source
        :return: int: 0 = internal, 1 = ext. adjustable, 2 = ext. TTL, (3 = something went wrong)
        """
        ts_string = self.__write_serial('ts?')  # returns string 'trigger source: internal/ext. adjustable/ext. TTL'
        print(ts_string)
        ts_val = 3  # global variable, place holder value
        if 'internal' in ts_string[-8:]:
            ts_val = 0  # variable is redefined as a local
        elif 'adjustable' in ts_string[-10:]:
            ts_val = 1  # variable is redefined as a local
        elif 'TTL' in ts_string[-3:]:
            ts_val = 2  # variable is redefined as a local
        else:
            print('Error: trigger source could not be determined. Try again!')
        return ts_val

    def set_trig_level(self, tl):
        """
        This is a function to set the trigger level
        :param tl: trigger level (-4800...+4800 mV)
        :return: float: trigger level (-4.80...+4.80 V)
        """
        self.__write_serial(f'tl={tl}', line_ending=b'\n')  # sets trigger level to tl (-4800...+4800 mV)
        return self.get_trig_level()

    def get_trig_level(self):
        """
        This is a function to get information about the set trigger level
        :return: float: trigger level (-4.80...+4.80 V)
        """
        tl_string = self.__write_serial('tl?')  # returns string 'trigger level: +0.00 V'
        print(tl_string)
        tl_val = float(tl_string[16:25])  # makes float from string of trigger level value
        return tl_val

    def set_tune_mode(self, tm):
        """
        This is a function to set the tune mode
        :param tm: tune mode (manual 0, auto 1)
        :return: int: 0 = manual, 1 = auto, (2 = something went wrong)
        """
        self.__write_serial(f'tm={tm}', line_ending=b'\n')  # sets tune mode to tm (manual 0, auto 1)
        return self.get_tune_mode()

    def get_tune_mode(self):
        """
        This is a function to get information about the set tune mode
        :return: int: 0 = manual, 1 = auto, (2 = something went wrong)
        """
        tm_string = self.__write_serial('tm?')  # returns string 'tune mode: manual/auto'
        print(tm_string)
        tm_val = 2  # global variable, place holder value
        if 'auto' in tm_string[-4:]:
            tm_val = 0  # variable is redefined as a local
        elif 'manual' in tm_string[-6:]:
            tm_val = 1  # variable is redefined as a local
        else:
            print('Error: tune mode could not be determined. Try again!')
        return tm_val

    def set_tune_value(self, tune):
        """
        This is a function to set a tune value
        It sets first the tune mode to manual
        :param tune: tune value (0...1000, where 1000=100 %)
        :return: float: tune value (0...100.0 %)
        """
        self.__write_serial('tm=0')  # sets tune mode to manual
        tune_mode_0 = self.get_tune_mode()
        print(tune_mode_0)
        self.__write_serial(f'tune={tune}', line_ending=b'\n')  # sets tune value to tune (0...1000, where 1000=100 %)
        return self.get_tune_value()

    def get_tune_value(self):
        """
        This is a function to get information about the set tune value
        :return: float: tune value (0...100.0 %)
        """
        tune_string = self.__write_serial('tune?')  # returns string 'tune value: 70.00 %'
        print(tune_string)
        tune_val = float(tune_string[15:24])
        return tune_val

    def set_freq(self, f):
        """
        This is a function to set the internal oscillator frequency
        :param f: frequency (25...125000000 Hz)
        :return: str: 'int. frequency: 100 Hz'
        """
        self.__write_serial(f'f={f}', line_ending=b'\n')  # sets frequency to f (25...125000000)
        return self.get_freq()

    def get_freq(self):
        """
        This is a function to get information about the set frequency
        :return: float: frequency (25...125000000 Hz)
        """
        freq_string = self.__write_serial('f?')  # returns string 'int. frequency: 100 Hz'
        print(freq_string)
        freq = float(freq_string[17:27])
        return freq

    def set_cwl(self, cwl):
        """
        This is a function to set the CW laser output power value
        :param cwl: CW laser output power (0...100 %)
        :return: float: CW laser output power (0...100 %)
        """
        self.__write_serial(f'cwl={cwl}', line_ending=b'\n')  # sets CW laser output power (0...100)
        return self.get_cwl()

    def get_cwl(self):
        """
        This is a function to get information about the CW laser output power value
        :return: float: CW laser output power (0...100 %)
        """
        cwl_string = self.__write_serial('cwl?')  # returns string 'CW output power: 0 %'
        print(cwl_string)
        cwl_val = float(cwl_string[16:19])
        return cwl_val

    def on_cw(self):
        """
        This is a function to enable the CW laser emission
        :return: int: 1 = on, (2 = something went wrong)
        """
        self.__write_serial('cw=1')  # enables CW laser emission
        return self.get_cw()

    def off_cw(self):
        """
        This is a function to disable the CW laser emission
        :return: int: 0 = off, (2 = something went wrong)
        """
        self.__write_serial('cw=0')  # disables CW laser emission
        return self.get_cw()

    def get_cw(self):
        """
        This is a function to get information about the CW laser emission state
        :return: int: 0 = off, 1 = on, (2 = something went wrong)
        """
        cw_string = self.__write_serial('cw?')  # returns string 'CW laser emission: off/on'
        print(cw_string)
        cw_val = 2  # global variable, place holder value
        if 'off' in cw_string[-3:]:
            cw_val = 0  # variable is redefined as a local
        elif 'on' in cw_string[-3:]:
            cw_val = 1  # variable is redefined as a local
        else:
            print('Error: CW laser emission state could not be determined. Try again!')
        return cw_val
