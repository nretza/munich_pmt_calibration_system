#!/usr/bin/python3
from devices.device import serial_device
import time


class HV_supply(serial_device):
    """
    Class for connecting to the HV base

    This is a Singleton - google it!
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = HV_supply()
        return cls._instance


    def __init__(self, dev="/dev/HV_Base", simulating=False, delay=.1):

        if HV_supply._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            HV_supply._instance = self

        super().__init__(dev=dev, simulating=simulating, delay=delay)

        self.vmax = 1400

        self.off()
        self.setHVMax(self.vmax)
        self.SetVoltage(1100)

    def on(self):
        pass
        return self.is_on()

    def off(self):
        pass
        return self.is_on()

    def is_on(self):
        pass

#-----------------------------------------------------------

    def SetVoltage(self, V:float, tolerance:float=1, max_iter:int=60, wait_time:float=1) -> float:
        if V > self.vmax:
            self.logger.warning(f"Voltage {V} V exceeds V_Max of {self.vmax} V. Setting voltage to V_Max instead.")
            V = self.vmax
        if not self.is_on():
            self.logger.warning(f"Cant set voltage, base is not turned on!")
            raise RuntimeError

        self.setHVSet(HV=V)

        iter = 0
        while self.getHVMon() - self.getHVSet() > tolerance:
            iter += 1
            time.sleep(wait_time)
            if iter >= max_iter:
                self.logger.warning("Voltage does not adjust in time, try to increase RampUP/RampDwn speed!")
                break

        return self.getHVMon()

#-----------------------------------------------------------

    def setHV_rampup_rate(self, rate:float):
        pass
        self.logger.debug(f"Setting RampUp-Rate to {rate} V/s")

    def getHV_rampup_rate(self) -> float:
        pass

    def setHV_rampdown_rate(self, rate:float):
        pass
        self.logger.debug(f"Setting RampDown-Rate to {rate} V/s")

    def getHV_rampdown_rate(self) -> float:
        pass

    def setHVSet(self, HV:float):
        pass
        self.logger.debug(f"setting HV to {HV} Volt")

    def getHVSet(self) -> float:
        pass

    def getHVMon(self) -> float:
        pass

    def getHVMax(self) -> float:
        pass

    def setHVMax(self, MaxV:float):
        pass
        self.logger.debug(f"setting Maximum HV to {MaxV} Volt")

    def setISet(self, I:float) -> float:
        pass
        self.logger.debug(f"setting current to {I} uA")

    def getISet(self) -> float:
        pass

    def getIMon(self) -> float:
        pass
