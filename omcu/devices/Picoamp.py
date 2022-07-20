#!/usr/bin/python3
import time
import numpy as np

from omcu.devices.device import serial_device


class Picoamp(serial_device):
    """
    This is a class for the Keithley 6482 Picoamperemeter

    This is a Singleton - google it!
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = Picoamp()
        return cls._instance

    def __init__(self, dev="/dev/Picoamp"):

        if Picoamp._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            Picoamp._instance = self

        super().__init__(dev=dev)

        startup = ['*RST', 'SENS:CURR:RANG:AUTO ON', 'SENS2:CURR:RANG:AUTO ON', 'SYST:AZER ON', 'SYST:AZER OFF']
        for i in startup:
            self.serial_io(i)
            time.sleep(1.0)

    #legacy support
    def read_ch1(self, ncal):
        return self.read_ch(1, ncal)

    #legacy support
    def read_ch2(self, ncal):
        return self.read_ch(2, ncal)


    def read_ch(self, ch, ncal):
        """
        This is a function to read out a channel of the Picoamperemter
        :param ncal: Take ncal measurements and then stop
        :return: val = np.array([])
        """

        assert ch in (1,2)

        self.serial_io(f'FORM:ELEM CURR{ch}')
        comms = []
        i = 1
        comms.append('TRIG:DEL 0')
        comms.append('ARM:COUN %s' % ncal)
        comms.append('INIT')
        comms.append('READ?')
        for comm in comms:
            line = self.serial_io(comm)
        val = np.array([])
        try:
            for x in line.split(',')[::2]:
                val = np.append(val, [float(x)])
        except:
            print("\tMeasurement failed, trying again...")
            i += 1
            if i >= 50:
                return np.nan, np.nan
        print(f'\tPhotodiode current Ch{ch}: {val} A' % val)
        # mean = np.mean(val)
        # std  = np.std(val) / np.sqrt(ncal)
        return val