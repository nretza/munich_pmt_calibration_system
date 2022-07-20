import sys
import argparse
import itertools

from omcu.devices.Picoscope import Picoscope
from omcu.devices.PSU import PSU0, PSU1
from omcu.devices.Picoamp import Picoamp
from omcu.devices.Rotation import Rotation
from omcu.devices.Laser import Laser
from omcu.devices.Powermeter import Powermeter
from omcu.devices.device import device, serial_device
from omcu.util import *

setup_file_logging(logging_file="logging.log", logging_level=20)

#Turn relevant devices on
PSU1.Instance().on()
Rotation.Instance().go_home()
Laser.Instance().on_pulsed()
HV_supply.Instance().on()

#time to reduce noise
time.sleep(1)

#tune parameters
tune_occ(0,0.05)
tune_gain(0.95*10e6, 1.05*10e6)


for phi, theta in itertools.product(np.arange(0, 90, 10), np.arange(0, 90, 10)):
    Rotation.Instance().set_position(phi, theta)
    print()
    print(f"moved to phi: {phi}, theta: {theta}")
    print(f"OCC:\t {measure_occ()}")
    print(f"gain:\t {measure_gain()}")