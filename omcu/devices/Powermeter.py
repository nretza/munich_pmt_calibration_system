#!/usr/bin/python3
from devices.device import serial_device

class Powermeter(serial_device):
    """
    This is a class for the Newport Optical Powermeter Model 2936-R
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = Powermeter()
        return cls._instance

    def __init__(self, dev="/dev/Powermeter", simulating=False, delay=.5):

        if Powermeter._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            Powermeter._instance = self

        super().__init__(dev=dev, simulating=simulating, delay=delay)

        self.set_echo(0)  # Echo off !!!
        self.set_lambda(405)  # The Picosecond Laser has a wavelength of 405 nm.
        self.set_channel(1)  # Power meter channel 1
        self.set_buffer(0)  # buffer with fixed size
        self.clear()  # Data Store cleared of all data
        self.set_mode(0)  # DC Contonuous
        self.set_interval(1)  # all measurements taken are put in the data store buffer
        self.set_run(1)  # enable data acquisition


    def set_echo(self, state):
        """
        This is a function to turn on or off the echoing of commands sent to the power meter.
        When the echo mode is enabled, the power meter generates a '>' prompt for every new line and all characters
        sent to the power meter are echoed back over the interface.
        When the echo mode is disabled (normal mode) the power meter does not generate a prompt or echo character
        back over the interface.
        !!! Do not use state = 1 (echo on) !!! The serial_io function cannot handle this
        :param state: int (0 = echo off, 1 = echo on)
        :return: int: 0 = echo off, 1 = echo on
        """

        self.serial_io(f'ECHO {state}')
        self.logger.info(f"set echo to {state}")
        return self.get_echo()

    def get_echo(self):
        """
        This is a function to get information about the echo set
        :return: int: 0 = echo off, 1 = echo on
        """
        echo_string = self.serial_io('echo?')  # returns the set echo (0,1)
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
        self.serial_io(f'PM:L {lamb}')
        self.logger.info(f"set lambda to {lamb}")
        return self.get_lambda()

    def get_lambda(self):
        """
        This is a function to get information about the selected wavelength
        :return: int: selected wavelength in nm
        """
        lamb_string = self.serial_io('PM:L?')  # returns the selected wavelength in nm
        self.logger.debug(f"The selected wavelength in nm is: {lamb_string}")
        lamb = int(lamb_string)
        return lamb

    def set_channel(self, ch):
        """
        This is a function to select the power meter channel.
        :param ch: 1/2 (power meter channel)
        :return: int: 1/2 (selected power meter channel)
        """
        self.serial_io(f'PM:CHAN {ch}')  # power meter channel
        self.logger.info(f"set channel to {ch}")
        return self.get_channel()

    def get_channel(self):
        """
        This is a function to get information about the selected power meter channel
        :return: int: 1/2 (selected power meter channel)
        """
        chan_string = self.serial_io('PM:CHAN?')  # returns the selected power meter channel
        self.logger.debug(f"The selected power meter channel is: {chan_string}")
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
        self.serial_io(f'PM:DS:BUF {buf}')  # buffer behavior
        self.logger.info(f"set buffer to {buf}")
        return self.get_buffer()

    def get_buffer(self):
        """
        This is a function to get information about the selected buffer behavior
        :return: int: 0 = fixed size, 1 = ring buffer
        """
        buff_string = self.serial_io('PM:DS:BUF?')  # returns the selected buffer behavior
        self.logger.debug(f"The selected buffer behavior is: {buff_string} (0 = fixed size, 1 = ring buffer)")
        buff = int(buff_string)
        return buff

    def clear(self):
        """
        This is a function to clear the Data Store of all data
        :return: -
        """
        self.serial_io('PM:DS:CL')  # resets the data store to be empty with no values
        self.logger.info("cleared data store of all data")

    def get_count(self):
        """
        This is a function to get information about the number of measurements that have been collected
        in the Data Store.
        :return: int (The number of measurements that have been collected)
        """
        count_string = self.serial_io('PM:DS:C?')  # returns the number of measurements collected
        self.logger.debug("The number of measurements that have been collected is:", count_string)
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
        self.serial_io(f'PM:DS:EN {en}')
        self.logger.info(f"set data collection to {en}")
        return self.get_collection_status()

    def get_collection_status(self):
        """
        This is a function to get the enabled status of the Data Store
        :return: status of the Data Store (0 = disable, 1 = enable)
        """
        collect_string = self.serial_io('PM:DS:EN?')  # returns the status of the collection in the Data Store
        self.logger.debug(f"The collection of measurements in the Data Store is: {collect_string} \
              (0 = disabled or buffer full (after 10000 measurements), 1 = enabled)")
        self.get_count()
        collect = int(collect_string)
        return collect

    def get_data(self, num):
        """
        This is a function to get a number of measurements that have been collected in the Data Store.
        :param num: str
                    “1”-returns the single value specified by index 1
                    “1-10”-returns values in the range from the indices 1-10
                    “-5”-returns the oldest 5 values (same as 1-5)
                    “+1”-returns the newest value
        :return: list of data (floats) with the length that was indicated with num
                looks something like this: [-1.295755E-011, -1.295711E-011, -1.295667E-011, -1.295623E-011]

        """
        s = self.serial_io(f'PM:DS:GET? {num}', multi_line=True)  # returns a number of measurements collected

        # print(s)    # prints something like this:
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
            if index > 11:
                if 'End of Data' in i or i == '':
                    pass
                else:
                    data_list.append(float(i))
            else:
                pass
        return data_list

    def set_interval(self, intv):
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
        :return: int (selected Data Store Interval)
        """
        self.serial_io(f'PM:DS:INT {intv}')  # selects the Data Store Interval
        self.logger.info(f"set inerval to {intv}")
        return self.get_interval()

    def get_interval(self):
        """
        This is a function to get information about the selected Data Store Interval
        :return: int (selected Data Store Interval)
        """
        intv_string = self.serial_io('PM:DS:INT?')  # returns the selected Data Store Interval
        self.logger.debug(f"The selected Data Store Interval is: {intv_string}")
        intv = int(intv_string)
        return intv

    def set_mode(self, mode):
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
        :return: int (present acquisition mode)
        """
        self.serial_io(f'PM:MODE {mode}')  # selects the acquisition mode
        self.logger.info(f"set mode to {mode}")
        return self.get_mode()

    def get_mode(self):
        """
        This is a function to get the present acquisition mode
        :return: int
                 0 = DC Continuous,
                 1 = DC Single,
                 2 = Integrate,
                 3 = Peak-to-peak Continuous,
                 4 = Peak-to-peak Single,
                 5 = Pulse Continuous,
                 6 = Pulse Single,
                 7 = RMS
        """
        mode_string = self.serial_io('PM:MODE?')  # returns the selected acquisition mode
        self.logger.debug(  f"The selected acquisition mode is: {mode_string}, \
                (0 = DC Continuous, 1 = DC Single, 2 = Integrate, 3 = Peak-to-peak Continuous, \
                4 = Peak-to-peak Single, 5 = Pulse Continuous, 6 = Pulse Single, 7 = RMS)")
        mode = int(mode_string)
        return mode

    def get_power(self):
        """
        This is a function to get the measured (and corrected) power in the selected units
        :return: float
        """
        power_string = self.serial_io('PM:P?')  # returns the power in the selected units
        #print("The power is:", power_string)
        power = float(power_string)
        return power

    def set_run(self, runner):
        """
        This is a function to disable or enable the acquisition of data
        :param runner: 0 = stopped, 1 = running
        :return: int (0 = stopped, 1 = running)
        """
        self.serial_io(f'PM:RUN {runner}')  # disables or enables the acquisition of data
        self.logger.info(f"set run to {runner}")
        return self.get_run()

    def get_run(self):
        """
        This is a function to get the present run mode
        :return: int (0 = stopped, 1 = running)
        """
        run_string = self.serial_io('PM:RUN?')  # returns an int indicating the present run mode
        run = int(run_string)
        return run

    def set_offset(self):
        """
        This is a function that sets the zeroing value with the present reading
        :return: float (set offset value)
        """
        self.serial_io('PM:ZEROSTO')  # sets the zeroing value with the present reading
        self.logger.info(f"set offset")
        return self.get_offset()

    def set_offset_val(self, offset):
        """
        This is a function that sets the zeroing value with the given value
        :param offset: float
        :return: float (set offset value)
        """
        self.serial_io(f'PM:ZEROVAL {offset}')  # sets the zeroing value with the given value
        self.logger.info(f"set offset to {offset}")
        return self.get_offset()

    def get_offset(self):
        """
        This is a function that returns the set offset value
        :return: float (set offset value)
        """
        offset_string = self.serial_io('PM:ZEROVAL?')  # returns
        self.logger.debug(f"The offset value is set to: {offset_string}")
        offset = float(offset_string)
        return offset