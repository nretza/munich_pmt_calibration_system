#!/usr/bin/python3
from devices.device import serial_device
import time


class HV_base(serial_device):
    """
    Class for connecting to the HV base

    This is a Singleton - google it!
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = HV_base()
        return cls._instance


    def __init__(self, dev="/dev/uBase", simulating=False, delay=.1):

        if HV_base._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            HV_base._instance = self

        super().__init__(dev=dev, simulating=simulating, delay=delay)

        self.vmax = 1400
        #self.setSleeping(False)
        #self.SetVoltage(0)


#-----------------------------------------------------------

    def SetVoltage(self, HV:float, tolerance:float=15, max_iter:int=60, wait_time:float=1) -> float:
        if HV > self.vmax:
            self.logger.warning(f"Voltage {HV} V exceeds V_Max of {self.vmax} V. Setting voltage to V_Max instead.")
            HV = self.vmax

        # output voltage is 12*Dy10
        Dy10 = round(HV/12)
        self.setDy10(Dy10)

        iter = 0
        while HV - self.getHV() > tolerance:
            iter += 1
            time.sleep(wait_time)
            if iter >= max_iter:
                self.logger.warning("Voltage does not adjust in time!")
                break

        return self.getHV()

#-----------------------------------------------------------

    def setDy10(self, Dy10:float):
        self.serial_io(f'Uquickscan {Dy10}')
        self.logger.debug(f"set Dy10 to {Dy10}")

    def getDy10(self):
        Dy10 = self.serial_io(f'Uget_avg_di10').strip()
        return float(Dy10)

    def getHV(self):
        HV = self.serial_io(f'Uget_avg_v10').strip() * 12
        return float(HV)
    def getUID(self):
        return self.serial_io(f'Uget_uid').strip()

    def setSleeping(self, sleep:bool):
        self.serial_io(f'Usleepenable {int(sleep)}')

    def getAvgReport(self):
        report = self.serial_io(f"Ureportavg", multi_line=True)
        return report.split("\n")