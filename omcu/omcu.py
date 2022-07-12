import sys
import argparse

sys.path.append('/home/canada/munich_pmt_calibration_system/omcu')

from devices.Picoscope import Picoscope
from devices.PSU import PSU0, PSU1
from devices.Picoamp import Picoamp
from devices.Rotation import Rotation
from devices.Laser import Laser
from devices.Powermeter import Powermeter


class omcu:

    def __init__(self, sim=True):

        """
        init for the omcu class
        devices are implemented as singletons
        """

        #call devices to initialize Singletons
        #Laser(simulating=sim)
        #Powermeter(simulating=sim)
        #Picoamp()
        #Picoscope()
        #PSU0()
        PSU1()
        Rotation()

        self.setup()


    def setup(self):

        """
        setup function for the ocmu. is supposed to tune the devices, and set a wait timers for all devices
        """

        PSU1.Instance().on()
        Rotation.Instance().go_home()



    def test_protokoll_1(self):
        pass

    def test_protokoll_2(self):
        pass

if __name__ == "__main__":
    OMCU = omcu()
    OMCU.setup()