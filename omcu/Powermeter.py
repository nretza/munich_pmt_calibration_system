import serial
import time


class Powermeter:
    """
    This is a class for the Newport Optical Powermeter Model 2936-R
    """

    def __init__(self, dev="/dev/Powermeter"):
        self.serial = serial.Serial(dev,
                                    baudrate=38400,
                                    bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE,
                                    timeout=2
                                    )
        self.set_echo(0)  # Echo OFF
        self.set_lambda(405)  # The Picosecond Laser has a wavelength of 405 nm.
        self.set_channel(1)  # Power meter channel 1

    def set_echo(self, state):
        """
        This is a function to turn on or off the echoing of commands sent to the power meter.
        When the echo mode is enabled, the power meter generates a '>' prompt for every new line and all characters
        sent to the power meter are echoed back over the interface.
        When the echo mode is disabled (normal mode) the power meter does not generate a prompt or echo character
        back over the interface.
        :param state: echo set (0 Echo OFF, 1 Echo ON)
        :return: echo status
        """
        self.serial.write(str.encode('ECHO %s\r\n' % state))  # 0 Echo OFF, 1 Echo ON
        time.sleep(.5)
        self.get_echo()

    def get_echo(self):
        """
        This is a function to get information about the echo set
        :return: 0 Echo OFF, 1 Echo ON
        """
        self.serial.write(b'ECHO?\r\n')  # returns the status of the echo
        time.sleep(.5)
        line = self.serial.readline()
        print("The Echo status is:", line.decode(), "(0 = Echo OFF, 1 = Echo ON)")

    def set_lambda(self, lamb):
        """
        This is a function to select the wavelength to use when calculating power.
        The value must fall within the calibrated wavelength of the detector.
        The Picosecond Laser has a wavelength of 405 nm.
        :param lamb: wavelength in nm
        :return: wavelength
        """
        self.serial.write(str.encode('PM:L %s\r\n' % lamb))  # wavelength set command
        time.sleep(.5)
        self.get_lambda()

    def get_lambda(self):
        """
        This is a function to get information about the selected wavelength
        :return: selected wavelength in nm
        """
        self.serial.write(b'PM:L?\r\n')  # returns the selected wavelength in nm
        time.sleep(.5)
        line = self.serial.readline()
        print("The selected wavelength in nm is:", line.decode())

    def set_channel(self, ch):
        """
        This is a function to select the power meter channel.
        :param ch: int (power meter channel)
        :return: currently selected power meter channel
        """
        self.serial.write(str.encode('PM:CHAN %s\r\n' % ch))  # power meter channel
        time.sleep(.5)
        self.get_channel()

    def get_channel(self):
        """
        This is a function to get information about the selected power meter channel
        :return: selected power meter channel
        """
        self.serial.write(b'PM:CHAN?\r\n')  # returns the selected power meter channel
        time.sleep(.5)
        line = self.serial.readline()
        print("The selected power meter channel is:", line.decode())

    def set_buffer(self, buf):
        """
        This is a function to select the behavior mode for control of the Data Store buffer.
        The behavior of the ring buffer is to allow continual data collection after the buffer is full
        where the oldest values will be overwritten when new measurements are taken.
        :param buf: 0 = fixed size, 1 = ring buffer
        :return:
        """
        self.serial.write(str.encode('PM:DS:BUF %s\r\n' % buf))  # buffer behavior
        time.sleep(.5)
        self.get_buffer()

    def get_buffer(self):
        """
        This is a function to get information about the selected buffer behavior
        :return: 0 = fixed size, 1 = ring buffer
        """
        self.serial.write(b'PM:DS:BUF?\r\n')  # returns the selected buffer behavior
        time.sleep(.5)
        line = self.serial.readline()
        print("The selected buffer behavior is:", line.decode(), "(0 = fixed size, 1 = ring buffer)")

    def clear(self):
        """
        This is a function to clear the Data Store of all data
        :return: -
        """
        self.serial.write(b'PM:DS:CL\r\n')  # resets the data store to be empty with no values
        time.sleep(.5)

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
        :return: int indicating the present acquisition mode
        """
        self.serial.write(str.encode('PM:MODE %s\r\n' % mode))  # selects the acquisition mode
        time.sleep(.5)
        self.get_mode()

    def get_mode(self):
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

    def get_count(self):
        """
        This is a function to get information about the number of measurements that have been collected
        in the Data Store.
        :return: int (The number of measurements that have been collected)
        """
        self.serial.write(b'PM:DS:C?\r\n')  # returns the number of measurements collected
        time.sleep(.5)
        line = self.serial.readline()
        print("The number of measurements that have been collected is:", line.decode())

    def set_data_collection(self, en):
        """
        This is a function to enable or disable the collection of measurements in the Data Store
        Data will be collected after the PM:DS:ENable command has been called with a parameter of 1.
        Data collection will stop when the PM:DS:ENable command has been called with a parameter of 0
        or when a fixed size data buffer is full.
        :param en: 0 = disable, 1 = enable
        :return: status of the Data Store (0 = disable, 1 = enable)
        """
        self.serial.write(str.encode('PM:DS:EN %s\r\n' % en))
        time.sleep(.5)
        self.get_collection_status()

    def get_collection_status(self):
        """
        This is a function to get the enabled status of the Data Store
        :return: status of the Data Store (0 = disable, 1 = enable)
        """
        self.serial.write(b'PM:DS:EN?\r\n')  # returns the enabled status of the Data Store
        time.sleep(.5)
        line = self.serial.readline()
        print("The enabled status of the Data Store is:", line.decode(), "(0 = disabled or buffer full, 1 = enabled)")

    def get_data(self, num):
        """
        This is a function to get a number of measurements that have been collected in the Data Store.
        :param num: 1, 1-10, -5, +5
        :return: “1”–returns the single value specified
                 “1-10”–returns values in the range from 1-10
                 “-5”–returns the oldest 5 values (same as 1-5)
                 “+5”–returns the newest 5 values
        """
        self.serial.write(str.encode('PM:DS:GET? %s\r\n' % num))  # returns a number of measurements collected
        time.sleep(.5)
        s = ''
        while self.serial.inWaiting():
            try:
                s += self.serial.read().decode()
            except:
                pass
        print(s)
