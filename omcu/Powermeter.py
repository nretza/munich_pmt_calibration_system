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

        self.echo(0)  # Echo OFF
        self.serial.write(b'PM:L 405\r\n')  # the Picosecond Laser has a wavelength of 405 nm

    def echo(self, state):
        """
        This is a function to turn on or off the echoing of commands sent to the power meter.
        When the echo mode is enabled, the power meter generates a '>' prompt for every new line and all characters
        sent to the power meter are echoed back over the interface.
        When the echo mode is disabled (normal mode) the power meter does not generate a prompt or echo character
        back over the interface.
        :param state: echo set (0 Echo OFF, 1 Echo ON)
        :return: echo status
        """
        self.serial.write(str.encode('ECHO %s\n' % state))  # 0 Echo OFF, 1 Echo ON
        time.sleep(.5)
        self.serial.write(str.encode('ECHO?\n'))  # returns the status of the echo
        time.sleep(.5)
        line = self.serial.readline()
        print("The Echo status is:", line.decode(), "(0 = Echo OFF, 1 = Echo ON)")
