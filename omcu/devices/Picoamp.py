#!/usr/bin/python3
import serial
import time
import numpy as np


class Picoamp:
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

        self.serial = serial.Serial(dev,
                                    baudrate=57600,
                                    bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE,
                                    timeout=2
                                    )
        startup = ['*RST', 'SENS:CURR:RANG:AUTO ON', 'SENS2:CURR:RANG:AUTO ON', 'SYST:AZER ON', 'SYST:AZER OFF']
        for i in startup:
            self.serial.write(str.encode('%s\r' % i))
            # print('\t%s' %i)
            time.sleep(1.0)

    def read_ch1(self, ncal):
        """
        This is a function to read out channel 1 of the Picoamperemter
        :param ncal: Take ncal measurements and then stop
        :return: val = np.array([])
        """
        self.serial.write(str.encode('FORM:ELEM CURR1'))
        comms = []
        i = 1
        comms.append(str.encode('TRIG:DEL 0\n'))
        comms.append(str.encode('ARM:COUN %s\n' % ncal))
        comms.append(str.encode('INIT\n'))
        comms.append(str.encode('READ?\n'))
        for comm in comms:
            # print('\t' + comm[:-1].decode("utf-8") )
            self.serial.write(comm)
            time.sleep(.1)
        line = self.serial.readline()
        # print(line)
        val = np.array([])
        try:
            for x in line.decode('utf8').split(',')[::2]:
                val = np.append(val, [float(x)])
        except:
            print("\tMeasurement failed, trying again...")
            i += 1
            if i >= 50:
                return np.nan, np.nan
        print('\tPhotodiode current Ch1: %s A' % val)
        # mean = np.mean(val)
        # std  = np.std(val) / np.sqrt(ncal)
        return val

    def read_ch2(self, ncal):
        """
        This is a function to read out channel 2 of the Picoamperemter
        :param ncal: Take ncal measurements and then stop
        :return: val = np.array([])
        """
        self.serial.write(str.encode('FORM:ELEM CURR2'))
        comms = []
        i = 1
        comms.append(str.encode('TRIG:DEL 0\n'))
        comms.append(str.encode('ARM:COUN %s\n' % ncal))
        comms.append(str.encode('INIT\n'))
        comms.append(str.encode('READ?\n'))
        for comm in comms:
            # print('\t' + comm[:-1].decode("utf-8") )
            self.serial.write(comm)
            time.sleep(.1)
        line = self.serial.readline()
        # print(line)
        val = np.array([])
        try:
            for x in line.decode('utf8').split(',')[::2]:
                val = np.append(val, [float(x)])
        except:
            print("\tMeasurement failed, trying again...")
            i += 1
            if i >= 50:
                return np.nan, np.nan
        print('\tPhotodiode current Ch2: %s A' % val)
        # mean = np.mean(val)
        # std  = np.std(val) / np.sqrt(ncal)
        return val


