#!/usr/bin/python3

import gpd3303s
import time


class PSU(gpd3303s.GPD3303S):
    """This class makes an instance for the USB power supply.
    It is important that the udev rules allow access to the current user.
    """

    def __init__(self, dev="/dev/PSU_0"):  # PSU_0 or PSU_1
        """
        This is the init function for the power supply device
        :param dev: device path, use: dev="/dev/PSU_0" or dev="/dev/PSU_1"
        """
        super().__init__()
        self.state = False
        self.open(dev)
        self.enableOutput(False)
        self.setCurrent(1, .1)
        self.setCurrent(2, .1)

    def ON(self):
        self.enableOutput(True)
        self.state = True
        time.sleep(1)

    def OFF(self):
        self.enableOutput(False)
        self.state = False


if __name__ == "__main__":
    p1 = PSU()
    p1.setVoltage(1, 10.0)
    print(p1.getVoltageOutput(1))
