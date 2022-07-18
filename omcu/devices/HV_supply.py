import pycaenhv.wrappers as hv_connection
from pycaenhv.enums import CAENHV_SYSTEM_TYPE, LinkType
from devices.device import device
import time

class HV_supply(device):
    """
    Class for connecting to the CAEN DT5533EM HV supply

    This is a Singleton - google it!
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = HV_supply()
        return cls._instance


    def __init__(self, system="DT55XX", link="USB_VCP", dev="ttyACM0"):

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

        self.hv_handle = hv_connection.init_system( system_type=11, #CAENHV_SYSTEM_TYPE[system], #DT55XXE
                                                    link_type=5, #LinkType[link], #USB_VCP
                                                    argument=args, #devie address
                                                    username="", #empty
                                                    password="" #empty
                                                  )
        self.hv_slot = 0

        print(hv_connection.get_crate_map(handle=self.hv_handle))
        print(hv_connection.get_board_parameters(self.hv_handle, self.hv_slot))
        print(hv_connection.get_channel_parameters(self.hv_handle, self.hv_slot, 1))



    def on(self, channel):
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "Pw", True)
        self.logger.Info(f"High Voltage on channel {channel} turned ON")

    def off(self, channel):
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "Pw", False)
        self.logger.Info(f"High Voltage on channel {channel} turned OFF")

    def off_all(self):
        for i in range(4):
            hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, 1, "Pw", False)
        self.logger.info("High Voltage on all channels turned OFF")

    def is_on(self, channel):
        hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "Pw")

#-----------------------------------------------------------

    def SetVoltage(self, channel, V, tolerance=5, max_iter=30, wait_time=2):
        if not self.is_on(channel):
            self.logger.warning(f"Cant set voltage, channel {channel} is not turned on!")
            raise RuntimeError

        self.setHVSet(channel, V)

        iter = 0
        while self.getHVMon(channel) - self.getHVSet(channel) > tolerance:
            iter += 1
            time.sleep(wait_time)
            if iter >= max_iter:
                self.logger.warning("Voltage does not adjust in time, try to increase RampUP/RampDwn speed!")
                break
        return self.getHVMon(channel)

#-----------------------------------------------------------

    def setHV_rampup_rate(self, channel, rate):
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "RUp", rate)
        self.logger.info(f"Setting RampUp-Rate for channel {channel} to {rate} V/s")

    def getHV_rampup_rate(self, channel):
        hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "RUp")
        pass

    def setHV_rampdown_rate(self, channel, rate):
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "RDwn", rate)
        self.logger.info(f"Setting RampDown-Rate for channel {channel} to {rate} V/s")

    def getHV_rampdown_rate(self, channel):
        hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "RDwn")

    def setHVSet(self, channel, HV):
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "VSet", HV)
        self.logger.info(f"setting HV on channel {channel} to {HV} Volt")

    def getHVSet(self, channel):
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "VSet")

    def getHVMon(self, channel):
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "VMon")

    def setISet(self, channel, I):
        hv_connection.set_channel_parameter(self.hv_handle, self.hv_slot, channel, "ISet", I)
        self.logger.info(f"setting current on channel {channel} to {I} Amp")

    def getISet(self, channel):
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "ISet")

    def getIMon(self, channel):
        return hv_connection.get_channel_parameter(self.hv_handle, self.hv_slot, channel, "IMon")
