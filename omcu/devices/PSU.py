#!/usr/bin/python3
import gpd3303s
import time


class PSU(gpd3303s.GPD3303S):
    """This class makes an instance for the USB power supply.
    It is important that the udev rules allow access to the current user.
    """

    def __init__(self, dev="/dev/PSU_1"):  # PSU_0 or PSU_1
        """
        This is the init function for the power supply device
        :param dev: device path, use: dev="/dev/PSU_0" or dev="/dev/PSU_1"
        """
        super().__init__()
        self.state = False
        self.open(dev)
        self.enableOutput(False)
        self.setCurrent(1, 3.0)
        self.setCurrent(2, .1)
        self.setVoltage(1, 12.0)
        self.setVoltage(2, 3.6)

    def settings(self, channel, voltage=5.0, current=0.1):
        """
        This is a function set voltage and current for the desired channel
        :param channel: int (1/2)
        :param voltage: float, default 5.0 V
        :param current: float, default 0.1 A
        :return: boolean (state)
        """
        self.setVoltage(channel, voltage)
        self.setCurrent(channel, current)
        return self.state

    def on(self):
        self.enableOutput(True)
        self.state = True
        time.sleep(1)

    def off(self):
        self.enableOutput(False)
        self.state = False


if __name__ == "__main__":
    P0 = PSU(dev="/dev/PSU_0")
    P0.setVoltage(1, 10.0)
    print(P0.getVoltageOutput(1))

