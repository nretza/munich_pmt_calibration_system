#!/usr/bin/python3
import logging

import serial
import time
import numpy as np


class SimSerial:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f'Initalised with - args: {args}; kwargs: {kwargs}')

    @staticmethod
    def readline():
        return 'test str /n'.encode()

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

    def __init__(self, dev="/dev/Laser_control", simulating=False):  # run sudo udevadm trigger before
        self.logger = logging.getLogger(type(self).__name__)

        # select if Serial or SimSerial
        if simulating:
            serial_connection = SimSerial
            self.delay = .01  # set default delay
        else:
            serial_connection = serial.Serial
            self.delay = .5  # set default delay

        # initialise Serial or SimSerial
        self.serial = serial_connection(dev,
                                        baudrate=19200,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout=2
                                        )

        self.OFF_pulsed()  # pulsed laser emission OFF
        self.set_trig_edge(1)  # trigger edge: rising
        self.set_trig_source(0)  # trigger source: internal
        self.set_trig_level(0)  # trigger level: 0 mV
        self.set_tune_mode(1)  # tune mode: auto
        self.set_freq(1000)  # frequency = 1 kHZ
        self.OFF_CW()  # CW laser emission OFF

    def __write_serial(self, cmd, delay=None, line_ending=b'\r\n'):
        if delay is None:
            delay = self.delay

        if type(cmd) is str:
            cmd = cmd.encode()

        if not cmd.endswith(line_ending):
            cmd += line_ending

        self.serial.write(cmd)
        time.sleep(delay)
        return self.serial.readline().decode()

    def get_state(self):
        """
        This function returns system state information
        """
        self.__write_serial('state?')
        s = ''
        while self.serial.inWaiting():
            try:
                s += self.serial.read().decode()
            except:
                pass
        return s

    def ON_pulsed(self):
        """
        This function enables the pulsed laser emission (laser ON)
        :return: first: information whether command was successfully executed
                second: information about emission state
        """
        self.__write_serial('ld=1')  # enables pulsed laser emission
        return self.get_ld()

    def OFF_pulsed(self):
        """
        This function disables the pulsed laser emission (laser OFF)
        :return: first: information whether command was successfully executed
                second: information about emission state
        """
        self.__write_serial('ld=0')  # disables pulsed laser emission
        return self.get_ld()

    def get_ld(self):
        """
        This is a function to get information about the pulsed laser emission state
        :return: pulsed laser emission state (on/off)
        """
        return self.__write_serial('ld?')  # returns pulsed laser emission state (on/off)

    def set_trig_edge(self, te):
        """
        This is a function to set the trigger edge
        :param te: trigger edge (rising 1, falling 0)
        :return: first: information whether command was successfully executed
                second: information about set trigger edge
        """
        self.__write_serial(f'te={te}', line_ending=b'\n')  # sets trigger edge to te (rising 1, falling 0)
        return self.get_trig_edge()

    def get_trig_edge(self):
        """
        This is a function to get information about the set trigger edge
        :return: trigger edge (rising/falling)
        """
        return self.__write_serial('te?')  # returns set trigger edge

    def set_trig_source(self, ts):
        """
        This is a function to set the trigger source
        :param ts: trigger source (internal 0, ext. adj. 1, ext. TTL 2)
        :return: first: information whether command was successfully executed
                second: information about set trigger source
        """
        # sets trigger source to ts (internal 0, ext. adj. 1, ext. TTL 2)
        self.__write_serial(f'ts={ts}', line_ending=b'\n')
        return self.get_trig_source()

    def get_trig_source(self):
        """
        This is a function to get information about the set trigger source
        :return: trigger source (internal/ext. adj./ext. TTL)
        """
        self.__write_serial('ts?')  # returns set trigger source

    def set_trig_level(self, tl):
        """
        This is a function to set the trigger level
        :param tl: trigger level (-4800...+4800 mV)
        :return: first: information whether command was successfully executed
                second: information about set trigger level
        """
        self.__write_serial(f'tl={tl}', line_ending=b'\n')  # sets trigger level to tl (-4800...+4800 mV)
        return self.get_trig_level()

    def get_trig_level(self):
        """
        This is a function to get information about the set trigger level
        :return: trigger level (-4800...+4800 mV)
        """
        return self.__write_serial('tl?')  # returns set trigger level

    def set_tune_mode(self, tm):
        """
        This is a function to set the tune mode
        :param tm: tune mode (auto 1, manual 0)
        :return: first: information whether command was successfully executed
                second: information about set tune mode
        """
        self.__write_serial(f'tm={tm}', line_ending=b'\n')  # sets tune mode to tm (auto 1, manual 0)
        return self.get_tune_mode()

    def get_tune_mode(self):
        """
        This is a function to get information about the set tune mode
        :return: tune mode (auto/manual)
        """
        return self.__write_serial('tm?')  # returns set tune mode (on/off)

    def set_tune_value(self, tune):
        """
        This is a function to set a tune value
        It sets first the tune mode to manual
        :param tune: tune value (0...1000)
        :return: first: information whether command was successfully executed (tune mode)
                second: information about set tune mode
                third: information whether command was successfully executed (tune value)
                fourth: information about set tune value
        """
        self.__write_serial('tm=0')  # sets tune mode to manual
        tune_mode_0 = self.get_tune_mode()
        self.__write_serial(f'tune={tune}', line_ending=b'\n')  # sets tune value to tune (0...1000)
        return tune_mode_0, self.get_tune_value()

    def get_tune_value(self):
        """
        This is a function to get information about the set tune value
        :return: tune value (0...1000)
        """
        return self.__write_serial('tune?')  # returns set tune value

    def set_freq(self, f):
        """
        This is a function to set the internal oscillator frequency
        :param f: frequency (25...125000000 Hz)
        :return: first: information whether command was successfully executed
                second: information about set frequency
        """
        self.__write_serial(f'f={f}', line_ending=b'\n')  # sets frequency to f (25...125000000)
        return self.get_freq()

    def get_freq(self):
        """
        This is a function to get information about the set frequency
        :return: frequency (25...125000000)
        """
        return self.__write_serial('f?')  # returns set frequency

    def ON_CW(self, cwl):
        """
        This is a function to set the CW laser output power and enable the emission
        :param cwl: CW laser output power (0...100)
        :return: first: information whether command was successfully executed (cwl)
                second: information about set CW laser output power
                third: information whether command was successfully executed (cw)
                fourth: information about set CW laser emission state
        """
        self.__write_serial(f'cwl={cwl}', line_ending=b'\n')  # sets CW laser output power (0...100)
        cw_0 = self.get_cwl()
        self.__write_serial('cw=1')  # enables CW laser emission
        return cw_0, self.get_cw()

    def OFF_CW(self):
        """
        This is a function to disable the CW laser emission
        :return: first: information whether command was successfully executed (cw)
                second: information about set CW laser emission state
        """
        self.__write_serial('cw=0')  # disables CW laser emission
        return self.get_cw()

    def get_cw(self):
        """
        This is a function to get information about the CW laser emission state
        :return: CW laser emission state (on/off)
        """
        return self.__write_serial('cw?')  # returns set CW laser emission state (on/off)

    def get_cwl(self):
        """
        This is a function to get information about the CW laser output power
        :return: CW laser output power (0...100)
        """
        return self.__write_serial('cwl?')  # returns set CW laser output power
