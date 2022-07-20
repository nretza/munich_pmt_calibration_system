import sys
import argparse

from omcu.devices.Picoscope import Picoscope
from omcu.devices.PSU import PSU0, PSU1
from omcu.devices.Picoamp import Picoamp
from omcu.devices.Rotation import Rotation
from omcu.devices.Laser import Laser
from omcu.devices.Powermeter import Powermeter
from omcu.devices.device import device, serial_device