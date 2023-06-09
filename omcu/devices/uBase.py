#!/usr/bin/python3
import time

from devices.device import serial_device


class uBase(serial_device):

    """
    Class for connecting to the uBase
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = uBase()
        return cls._instance


    def __init__(self, dev="/dev/uBase", simulating=False, delay=.1):

        if uBase._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            uBase._instance = self

        super().__init__(dev=dev, simulating=simulating, delay=delay)

        self.vmax = 120
        self.setSleeping(0)


#-----------------------------------------------------------

    def SetVoltage(self, Voltage:float, tolerance:float=0.1, max_iter:int=60, wait_time:float=1, initial_wait:float=5) -> float:

        self.logger.info(f"setting Dy10 voltage to {Voltage} V")
        if Voltage > self.vmax:
            self.logger.warning(f"Voltage {Voltage} V exceeds V_Max of {self.vmax} V. Setting voltage to V_Max instead.")
            Voltage = self.vmax

        # output voltage is 12*Dy10
        Dy10 = round(Voltage)    
        self.setDy10(Dy10)

        time.sleep(initial_wait)

        iter = 0
        while abs(Voltage - self.getDy10()) > tolerance:
            iter += 1
            time.sleep(wait_time)
            if iter >= max_iter:
                self.logger.warning("Voltage does not adjust in time!")
                break

        return self.getDy10()

#-----------------------------------------------------------

    def setDy10(self, Dy10:int):
        self.serial_io(f'Uquickscan {Dy10}')
        self.logger.debug(f"set Dy10 to {Dy10}")

    def getDy10(self):
        Dy10 = self.serial_io(f'Uget_avg_v10').strip()
        return float(Dy10)

    def getDi10(self):
        Di10 = self.serial_io(f'Uget_avg_di10').strip()
        return float(Di10)

    def getISup(self):
        ISup = self.serial_io(f'Uget_avg_isup').strip()
        return float(ISup)

    def getVSup(self):
        VSup = self.serial_io(f'Uget_avg_vsup').strip()
        return float(VSup)

    def getFrac(self):
        frac = self.serial_io(f'Uget_avg_frac').strip()
        return float(frac)

    def getUID(self):
        return self.serial_io(f'Uget_uid').strip()

    def setSleeping(self, sleep:bool):
        self.serial_io(f'Usleepenable {int(sleep)}')

    def getAvgReport(self):
        report = self.serial_io(f"Ureportavg", multi_line=True)
        return report.split("\n")