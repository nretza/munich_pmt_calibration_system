#!/usr/bin/python3
import logging
import serial
import time

from .SimSerial import SimSerial


class Powermeter:
    """
    This is a class for the Newport Optical Powermeter Model 2936-R
    """

    def __init__(self, dev="/dev/Powermeter", simulating=False, delay=.5):
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
                                        baudrate=38400,
                                        bytesize=serial.EIGHTBITS,
                                        parity=serial.PARITY_NONE,
                                        timeout=2
                                        )
        self.set_echo(0)  # Echo off !!!
        self.set_lambda(405)  # The Picosecond Laser has a wavelength of 405 nm.
        self.set_channel(1)  # Power meter channel 1

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

        while True:
            return_str = self.serial.readline().decode()
            self.logger.debug(f'Serial write cmd: {cmd}; return {return_str}')
            return return_str

    def set_echo(self, state):
        """
        This is a function to turn on or off the echoing of commands sent to the power meter.
        When the echo mode is enabled, the power meter generates a '>' prompt for every new line and all characters
        sent to the power meter are echoed back over the interface.
        When the echo mode is disabled (normal mode) the power meter does not generate a prompt or echo character
        back over the interface.
        !!! Do not use state = 1 (echo on) !!! The __write_serial function cannot handle this
        :param state: int (0 = echo off, 1 = echo on)
        :return: int: 0 = echo off, 1 = echo on
        """
        self.__write_serial(str.encode('ECHO %s\r\n' % state))
        return self.get_echo()

    def get_echo(self):
        """
        This is a function to get information about the echo set
        :return: int: 0 = echo off, 1 = echo on
        """
        echo_string = self.__write_serial(b'echo?\r\n')  # returns the set echo (0,1)
        print("The echo status is:", echo_string, "(0 = echo off, 1 = echo on)")
        echo = int(echo_string)
        return echo

    def set_lambda(self, lamb):
        """
        This is a function to select the wavelength to use when calculating power.
        The value must fall within the calibrated wavelength of the detector.
        The Picosecond Laser has a wavelength of 405 nm.
        :param lamb: int (wavelength in nm)
        :return: int: selected wavelength in nm
        """
        self.__write_serial(str.encode('PM:L %s\r\n' % lamb))
        return self.get_lambda()

    def get_lambda(self):
        """
        This is a function to get information about the selected wavelength
        :return: int: selected wavelength in nm
        """
        lamb_string = self.__write_serial(b'PM:L?\r\n')  # returns the selected wavelength in nm
        print("The selected wavelength in nm is:", lamb_string)
        lamb = int(lamb_string)
        return lamb

    def set_channel(self, ch):
        """
        This is a function to select the power meter channel.
        :param ch: 1/2 (power meter channel)
        :return: int: 1/2 (selected power meter channel)
        """
        self.__write_serial(str.encode('PM:CHAN %s\r\n' % ch))  # power meter channel
        return self.get_channel()

    def get_channel(self):
        """
        This is a function to get information about the selected power meter channel
        :return: int: 1/2 (selected power meter channel)
        """
        chan_string = self.__write_serial(b'PM:CHAN?\r\n')  # returns the selected power meter channel
        print("The selected power meter channel is:", chan_string)
        chan = int(chan_string)
        return chan

    def set_buffer(self, buf):
        """
        This is a function to select the behavior mode for control of the Data Store buffer.
        The behavior of the ring buffer is to allow continual data collection after the buffer is full
        where the oldest values will be overwritten when new measurements are taken.
        :param buf: int (0 = fixed size, 1 = ring buffer)
        :return: int: 0 = fixed size, 1 = ring buffer
        """
        self.__write_serial(str.encode('PM:DS:BUF %s\r\n' % buf))  # buffer behavior
        return self.get_buffer()

    def get_buffer(self):
        """
        This is a function to get information about the selected buffer behavior
        :return: int: 0 = fixed size, 1 = ring buffer
        """
        buff_string = self.__write_serial(b'PM:DS:BUF?\r\n')  # returns the selected buffer behavior
        print("The selected buffer behavior is:", buff_string, "(0 = fixed size, 1 = ring buffer)")
        buff = int(buff_string)
        return buff

    def clear(self):
        """
        This is a function to clear the Data Store of all data
        :return: -
        """
        self.__write_serial(b'PM:DS:CL\r\n')  # resets the data store to be empty with no values
        print("The Data Store has been cleared of all data")

    def get_count(self):
        """
        This is a function to get information about the number of measurements that have been collected
        in the Data Store.
        :return: int (The number of measurements that have been collected)
        """
        count_string = self.__write_serial(b'PM:DS:C?\r\n')  # returns the number of measurements collected
        print("The number of measurements that have been collected is:", count_string)
        count = int(count_string)
        return count

    def set_data_collection(self, en):
        """
        This is a function to enable or disable the collection of measurements in the Data Store
        Data will be collected after the PM:DS:ENable command has been called with a parameter of 1.
        Data collection will stop when the PM:DS:ENable command has been called with a parameter of 0
        or when a fixed size data buffer is full.
        :param en: 0 = disable, 1 = enable
        :return: status of the Data Store (0 = disabled, 1 = enabled)
        """
        self.__write_serial(str.encode('PM:DS:EN %s\r\n' % en))
        return self.get_collection_status()

    def get_collection_status(self):
        """
        This is a function to get the enabled status of the Data Store
        :return: status of the Data Store (0 = disable, 1 = enable)
        """
        collect_string = self.__write_serial(b'PM:DS:EN?\r\n')  # returns the status of the collection in the Data Store
        print("The collection of measurements in the Data Store is:", collect_string,
              "(0 = disabled or buffer full (after 1000 measurements), 1 = enabled)")
        self.get_count()
        collect = int(collect_string)
        return collect

    def get_data(self, num):
        """
        This is a function to get a number of measurements that have been collected in the Data Store.
        :param num: int/range
                    “1”–returns the single value specified
                    “1-10”–returns values in the range from 1-10
                    “-5”–returns the oldest 5 values (same as 1-5)
                    “+5”–returns the newest 5 values
        :return: list of data with the length that was indicated with num
                looks something like this: ['-1.295755E-011', '-1.295711E-011', '-1.295667E-011', '-1.295623E-011']

        """
        self.__write_serial(str.encode('PM:DS:GET? %s\r\n' % num))  # returns a number of measurements collected
        s = ''
        while self.serial.inWaiting():
            try:
                s += self.serial.read().decode()
            except:
                pass
        print(s)    # prints something like this:
                    # Detector SN: 2003
                    # IDN: NEWPORT 2936-R v1.2.3 08/04/15 SN24777
                    # Wavelength: 405
                    # Attenuator Status: Off
                    # Range Mode: Auto
                    # Store Interval: 1
                    # Analog Filter: 12.5kHz
                    # Digital Filter: 1000
                    # Mode: CW Continuous
                    # Responsivity: 1.737366E-001
                    # Units: W
                    # End of Header
                    # -1.295755E-011
                    # -1.295711E-011
                    # -1.295667E-011
                    # -1.295623E-011
                    # End of Data
        data_info_string = s
        data_info_list = data_info_string.split('\r\n')
        data_list = []
        for index, i in enumerate(data_info_list):
            if index >= 12:
                if index < (len(data_info_list)-2):
                    data_list.append(i)
                if index >= (len(data_info_list)-2):
                    pass
            else:
                pass
        return data_info_list, data_list

    def set_interval(self, intv):  #TODO: __write_serial
        """
        This is a function to select the Data Store Interval.
        An interval value of 1 causes the power meter to put all measurements taken in the data store buffer;
        a value of 2 causes every other measurement to be put in the data buffer and so on.
        If the measurement mode is “CW Continuous”, an interval setting of 1 translates to putting measurements
        at the rate of 0.1ms in the data buffer.
        If the measurement mode is “Peak-Peak Continuous”, an interval setting of 1 translates to putting measurements
        at a rate dictated by measurement timeout duration.
        If the measurement mode is “Pulse Continuous”,an interval setting of 1 translates to putting every pulse
        measurement in the data buffer.  Here, the rate of data storage depends upon the pulse repetition rate.
        The total time taken to fill up the data buffer depends upon various factors such as the interval,
        data store size and measurement mode.
        :param intv: int (represents the rate at which measurements are put in the data buffer)
        :return: selected Data Store Interval
        """
        self.serial.write(str.encode('PM:DS:INT %s\r\n' % intv))  # selects the Data Store Interval
        time.sleep(.5)
        self.get_interval()

    def get_interval(self):  #TODO: __write_serial
        """
        This is a function to get information about the selected Data Store Interval
        :return: selected Data Store Interval
        """
        self.serial.write(b'PM:DS:INT?\r\n')  # returns the selected Data Store Interval
        time.sleep(.5)
        line = self.serial.readline()
        print("The selected Data Store Interval is:", line.decode())

    def set_mode(self, mode):  #TODO: __write_serial
        """
        This is a function to select the acquisition mode for acquiring subsequent readings
        :param mode: 0 = DC Continuous,
                     1 = DC Single,
                     2 = Integrate,
                     3 = Peak-to-peak Continuous,
                     4 = Peak-to-peak Single,
                     5 = Pulse Continuous,
                     6 = Pulse Single,
                     7 = RMS
        :return: int indicating the present acquisition mode
        """
        self.serial.write(str.encode('PM:MODE %s\r\n' % mode))  # selects the acquisition mode
        time.sleep(.5)
        self.get_mode()

    def get_mode(self):  #TODO: __write_serial
        """
        This is a function to get the present acquisition mode
        :return: 0 = DC Continuous,
                 1 = DC Single,
                 2 = Integrate,
                 3 = Peak-to-peak Continuous,
                 4 = Peak-to-peak Single,
                 5 = Pulse Continuous,
                 6 = Pulse Single,
                 7 = RMS
        """
        self.serial.write(b'PM:MODE?\r\n')  # returns the selected acquisition mode
        time.sleep(.5)
        line = self.serial.readline()
        print("The selected acquisition mode is:", line.decode(),
              "(0 = DC Continuous, 1 = DC Single, 2 = Integrate, 3 = Peak-to-peak Continuous,"
              "4 = Peak-to-peak Single, 5 = Pulse Continuous, 6 = Pulse Single, 7 = RMS)")

    def get_power(self):  #TODO: __write_serial
        """
        This is a function to get the measured (and corrected) power in the selected units
        :return: exp (i.e. 9.4689E-04)
        """
        self.serial.write(b'PM:P?\r\n')  # returns the power in the selected units
        time.sleep(.5)
        line = self.serial.readline()
        print("The power is:", line.decode())

    def set_run(self, runner):  #TODO: __write_serial
        """
        This is a function to disable or enable the acquistion of data
        :param runner: 0 = stopped, 1 = running
        :return: int (0 = stopped, 1 = running)
        """
        self.serial.write(str.encode('PM:RUN %s\r\n' % runner))  # disables or enables the acquisition of data
        time.sleep(.5)
        self.get_run()

    def get_run(self):  #TODO: __write_serial
        self.serial.write(b'PM:RUN?\r\n')  # returns an int indicating the present run mode
        time.sleep(.5)
        line = self.serial.readline()
        print("The run mode is:", line.decode(), "(0 = stopped, 1 = running)")