#!/usr/bin/python3
import serial
import time


class Laser:
    """
    This is a class for the Picosecond Laser System Controller EIG2000DX
    """

    def __init__(self, dev="/dev/Laser_control"):  # run sudo udevadm trigger before
        self.serial = serial.Serial(dev,
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

    def get_state(self):
        """
        This function returns system state information
        """
        self.serial.write(b'state?\r\n')
        time.sleep(.5)
        s = ''
        while self.serial.inWaiting():
            try:
                s += self.serial.read().decode()
            except:
                pass
        print(s)

    def ON_pulsed(self):
        """
        This function enables the pulsed laser emission (laser ON)
        :return: first: information whether command was successfully executed
                second: information about emission state
        """
        self.serial.write(b'ld=1\r\n')  # enables pulsed laser emission
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_ld()

    def OFF_pulsed(self):
        """
        This function disables the pulsed laser emission (laser OFF)
        :return: first: information whether command was successfully executed
                second: information about emission state
        """
        self.serial.write(b'ld=0\r\n')  # disables pulsed laser emission
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_ld()

    def get_ld(self):
        """
        This is a function to get information about the pulsed laser emission state
        :return: pulsed laser emission state (on/off)
        """
        self.serial.write(b'ld?\r\n')  # returns pulsed laser emission state (on/off)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

    def set_trig_edge(self, te):
        """
        This is a function to set the trigger edge
        :param te: trigger edge (rising 1, falling 0)
        :return: first: information whether command was successfully executed
                second: information about set trigger edge
        """
        self.serial.write(str.encode('te=%s\n' % te))  # sets trigger edge to te (rising 1, falling 0)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_trig_edge()

    def get_trig_edge(self):
        """
        This is a function to get information about the set trigger edge
        :return: trigger edge (rising/falling)
        """
        self.serial.write(b'te?\r\n')  # returns set trigger edge
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

    def set_trig_source(self, ts):
        """
        This is a function to set the trigger source
        :param ts: trigger source (internal 0, ext. adj. 1, ext. TTL 2)
        :return: first: information whether command was successfully executed
                second: information about set trigger source
        """
        self.serial.write(str.encode('ts=%s\n' % ts))  # sets trigger source to ts (internal 0, ext. adj. 1, ext. TTL 2)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_trig_source()

    def get_trig_source(self):
        """
        This is a function to get information about the set trigger source
        :return: trigger source (internal/ext. adj./ext. TTL)
        """
        self.serial.write(b'ts?\r\n')  # returns set trigger source
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

    def set_trig_level(self, tl):
        """
        This is a function to set the trigger level
        :param tl: trigger level (-4800...+4800 mV)
        :return: first: information whether command was successfully executed
                second: information about set trigger level
        """
        self.serial.write(str.encode('tl=%s\n' % tl))  # sets trigger level to tl (-4800...+4800 mV)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_trig_level()

    def get_trig_level(self):
        """
        This is a function to get information about the set trigger level
        :return: trigger level (-4800...+4800 mV)
        """
        self.serial.write(b'tl?\r\n')  # returns set trigger level
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

    def set_tune_mode(self, tm):
        """
        This is a function to set the tune mode
        :param tm: tune mode (auto 1, manual 0)
        :return: first: information whether command was successfully executed
                second: information about set tune mode
        """
        self.serial.write(str.encode('tm=%s\n' % tm))  # sets tune mode to tm (auto 1, manual 0)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_tune_mode()

    def get_tune_mode(self):
        """
        This is a function to get information about the set tune mode
        :return: tune mode (auto/manual)
        """
        self.serial.write(b'tm?\r\n')  # returns set tune mode (on/off)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

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
        self.serial.write(b'tm=0\r\n')  # sets tune mode to manual
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_tune_mode()
        self.serial.write(str.encode('tune=%s\n' % tune))  # sets tune value to tune (0...1000)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_tune_value()

    def get_tune_value(self):
        """
        This is a function to get information about the set tune value
        :return: tune value (0...1000)
        """
        self.serial.write(b'tune?\r\n')  # returns set tune value
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

    def set_freq(self, f):
        """
        This is a function to set the internal oscillator frequency
        :param f: frequency (25...125000000 Hz)
        :return: first: information whether command was successfully executed
                second: information about set frequency
        """
        self.serial.write(str.encode('f=%s\n' % f))  # sets frequency to f (25...125000000)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_freq()

    def get_freq(self):
        """
        This is a function to get information about the set frequency
        :return: frequency (25...125000000)
        """
        self.serial.write(b'f?\r\n')  # returns set frequency
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

    def ON_CW(self, cwl):
        """
        This is a function to set the CW laser output power and enable the emission
        :param cwl: CW laser output power (0...100)
        :return: first: information whether command was successfully executed (cwl)
                second: information about set CW laser output power
                third: information whether command was successfully executed (cw)
                fourth: information about set CW laser emission state
        """
        self.serial.write(str.encode('cwl=%s\n' % cwl))  # sets CW laser output power (0...100)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_cwl()
        self.serial.write(b'cw=1\r\n')  # enables CW laser emission
        time.sleep(1.0)
        line = self.serial.readline()
        print(line.decode())
        self.get_cw()

    def OFF_CW(self):
        """
        This is a function to disable the CW laser emission
        :return: first: information whether command was successfully executed (cw)
                second: information about set CW laser emission state
        """
        self.serial.write(b'cw=0\r\n')  # disables CW laser emission
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
        self.get_cw()

    def get_cw(self):
        """
        This is a function to get information about the CW laser emission state
        :return: CW laser emission state (on/off)
        """
        self.serial.write(b'cw?\r\n')  # returns set CW laser emission state (on/off)
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())

    def get_cwl(self):
        """
        This is a function to get information about the CW laser output power
        :return: CW laser output power (0...100)
        """
        self.serial.write(b'cwl?\r\n')  # returns set CW laser output power
        time.sleep(.5)
        line = self.serial.readline()
        print(line.decode())
