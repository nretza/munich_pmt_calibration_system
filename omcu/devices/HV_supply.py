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
        commstop = "1"
        commparity = "0"
        lbusaddress = "1-3.4.4.4.2:1.0"
        args="_".join([dev,baudrate,commdata,commstop,commparity, lbusaddress])

        self.hv_handle = hv_connection.init_system( system_type=9, #CAENHV_SYSTEM_TYPE[system], #DT55XX
                                                    link_type=5, #LinkType[link], #USB_VCP
                                                    argument=args, #devie address
                                                    username="", #empty
                                                    password="" #empty
                                                  )
        self.create_map = hv_connection.get_crate_map(handle=self.hv_handle)
        self.off(channel=4)

    def on(self, channel):
        pass

    def off(self, channel):
        pass

    def setHV_rampup_rate(self, channel, rate):
        pass

    def getHV_rampup_rate(self, channel, rate):
        pass

    def setHV_rampdown_rate(self, channel, rate):
        pass

    def getHV_rampdown_rate(self):
        pass

    def setHV(self, Channel, HV):
        pass

    def getHV(self, channel, HV):
        pass

    def setCurrent(self, channel, curr):
        pass

    def getCurrent(self, channel, curr):
        pass


    def print_map(self):
        print(self.create_map)