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

    def echo_on(self):
        """
        This is a function to turn on the echoing of commands sent to the power meter.
        When the echo mode is enabled, the power meter generates a '>' prompt for every new line and all characters
        sent to the power meter are echoed back over the interface.
        """
        self.serial.write(str.encode('ECHO ON'))
        time.sleep(.1)
        line = self.serial.readline()
        print(line.decode())
        self.serial.write(str.encode('ECHO?'))  # returns the status of the echo
        time.sleep(.1)
        line = self.serial.readline()
        print(line.decode())

    def echo_off(self):
        """
        This is a function to turn off the echoing of commands sent to the power meter.
        When the echo mode is disabled (normal mode) the power meter does not generate a prompt or echo character
        back over the interface.
        """
        self.serial.write(str.encode('ECHO OFF'))
        time.sleep(.1)
        line = self.serial.readline()
        print(line.decode())
        self.serial.write(str.encode('ECHO?'))  # returns the status of the echo
        time.sleep(.1)
        line = self.serial.readline()
        print(line.decode())
