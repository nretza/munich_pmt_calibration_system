#!/usr/bin/python3
import gpd3303s
import time


class PSU(gpd3303s.GPD3303S):
    """This class makes an instance for the USB power supply.
    It is important that the udev rules allow access to the current user.
    """

    def __init__(self, dev):
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
        self.logger.debug(f"set settings. ch: {channel}, voltage: {voltage}, current: {current}")
        return self.state

    def on(self):
        self.enableOutput(True)
        self.state = True
        self.logger.info("turned on")
        time.sleep(1)

    def off(self):
        self.enableOutput(False)
        self.logger.info("turned off")
        self.state = False

    def is_on(self):
        return self.state

class PSU0(PSU):
    
    """
    PSU0 implemented as Singleton child class of PSU
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = PSU0()
        return cls._instance

    def __init__(self, dev="/dev/PSU_0"):

        if PSU0._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            PSU0._instance = self

        super().__init__(dev)
        #self.state = False
        #self.open(dev)
        #self.enableOutput(False)
        #self.setCurrent(1, 3.0)
        #self.setCurrent(2, .1)
        #self.setVoltage(1, 12.0)
        #self.setVoltage(2, 3.6)

class PSU1(PSU):

    """
    PSU1 implemented as Singleton child class of PSU
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = PSU1()
        return cls._instance

    def __init__(self, dev="/dev/PSU_1"):

        if PSU1._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            PSU1._instance = self

        super().__init__(dev)
        #self.state = False
        #self.open(dev)
        #self.enableOutput(False)
        #self.setCurrent(1, 3.0)
        #self.setCurrent(2, .1)
        #self.setVoltage(1, 12.0)
        #self.setVoltage(2, 3.6)