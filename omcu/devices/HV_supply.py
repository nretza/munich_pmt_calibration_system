#!/usr/bin/python3
import pycaenhv.wrappers as hv_connection
from devices.device import device
import time


class HV_supply(device):

    """
    Class for connecting to the CAEN DT5533EM HV supply
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = HV_supply()
        return cls._instance


    def __init__(self, dev:str="ttyACM0", default_ch:int=2):

        if HV_supply._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            HV_supply._instance = self

        super().__init__()

        baudrate = "9600"
        commdata = "8"
        commstop = "0"
        commparity = "0"
        args="_".join([dev,baudrate,commdata,commstop,commparity])

        self.default_ch = default_ch # This is the default channel, i.e. the channel the PMT is connected to
        
        self.hv_handle = hv_connection.init_system( system_type=11, #CAENHV_SYSTEM_TYPE[system], #DT55XXE
                                                    link_type=5,    #LinkType[link], #USB_VCP
                                                    argument=args,  #devie address
                                                    username="",    #empty
                                                    password=""     #empty
                                                  )
        self.hv_slot = 0
        self.vmax = 1400

        self.off_all()
        for channel in range(4):
            self.setHV_rampup_rate(100, channel)
            self.setHV_rampdown_rate(100, channel)
            self.setHVSet(1000, channel)
            self.setISet(150, channel)
            self.setHVMax(self.vmax + 10, channel)

    def on(self, channel:int=None):
        if not channel:
            channel = self.default_ch
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "Pw", True)
        self.logger.info(f"High Voltage on channel {channel} turned ON")
        return self.is_on(channel)

    def off(self, channel:int=None):
        if not channel:
            channel = self.default_ch
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "Pw", False)
        self.logger.info(f"High Voltage on channel {channel} turned OFF")
        return self.is_on(channel)

    def off_all(self):
        for i in range(4):
            hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, i, "Pw", False)
        self.logger.info("High Voltage on all channels turned OFF")

    def is_on(self, channel:int=None):
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "Pw")

#-----------------------------------------------------------

    def SetVoltage(self, V:float, channel:int=None, tolerance:float=1, max_iter:int=60, wait_time:float=1) -> float:
        if V > self.vmax:
            self.logger.warning(f"Voltage {V} V exceeds V_Max of {self.vmax} V. Setting voltage to V_Max instead.")
            V = self.vmax
        if not channel:
            channel = self.default_ch
        if not self.is_on(channel):
            self.logger.warning(f"Cant set voltage, channel {channel} is not turned on!")
            raise RuntimeError

        self.setHVSet(HV=V, channel=channel)
        self.logger.debug(f"Set voltage on channel {channel} to {V} Volt")

        iter = 0
        while self.getHVMon(channel) - self.getHVSet(channel) > tolerance:
            iter += 1
            time.sleep(wait_time)
            if iter >= max_iter:
                self.logger.warning("Voltage does not adjust in time, try to increase RampUP/RampDwn speed!")
                break

        return self.getHVMon(channel)

#-----------------------------------------------------------

    def setHV_rampup_rate(self, rate:float, channel:int=None):
        if not channel:
            channel = self.default_ch
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "RUp", rate)
        self.logger.debug(f"Setting RampUp-Rate for channel {channel} to {rate} V/s")

    def getHV_rampup_rate(self, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "RUp")

    def setHV_rampdown_rate(self, rate:float, channel:int=None):
        if not channel:
            channel = self.default_ch
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "RDwn", rate)
        self.logger.debug(f"Setting RampDown-Rate for channel {channel} to {rate} V/s")

    def getHV_rampdown_rate(self, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "RDwn")

    def setHVSet(self, HV:float, channel:int=None):
        if not channel:
            channel = self.default_ch
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "VSet", HV)
        self.logger.debug(f"setting HV on channel {channel} to {HV} Volt")

    def getHVSet(self, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "VSet")

    def getHVMon(self, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "VMon")

    def getHVMax(self, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "MaxV")

    def setHVMax(self, MaxV:float, channel:int=None):
        if not channel:
            channel = self.default_ch
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "MaxV", MaxV)
        self.logger.debug(f"setting Maximum HV on channel {channel} to {MaxV} Volt")

    def setISet(self, I:float, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "ISet", I)
        self.logger.debug(f"setting current on channel {channel} to {I} uA")

    def getISet(self, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "ISet")

    def getIMon(self, channel:int=None) -> float:
        if not channel:
            channel = self.default_ch
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "IMon")
