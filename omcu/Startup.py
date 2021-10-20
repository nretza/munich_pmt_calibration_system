#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Rotation import Rotation
from submodules.Picoamp import Picoamp
from submodules.Laser import Laser
from submodules.Powermeter import Powermeter
import time

Ps = Picoscope()
Psu0 = PSU(dev="/dev/PSU_0")
Psu1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()
Pa = Picoamp()
L = Laser()
Pm = Powermeter()

time.sleep(300)  # wait 5 minutes so that it's dark
Pm.set_offset()  # set offset value when it's dark
Pa_data_dark = Pa.read_ch1(100)  # value? data collection of Picoamp

Psu0.settings(1, voltage=12.0, current=3.0)  # psu for rotation stage
Psu1.settings(1, voltage=5.0, current=0.1)  # psu for PMT, Vcc
Psu1.settings(2, voltage=1.1, current=0.1)  # psu for PMT, Vcontrol
Psu0.on()
Rot.go_home()
Psu1.on()

L.set_freq(f=1000000)  # value?
L.set_tune_value(tune=700)  # value?
L.on_pulsed()  # pulsed laser emission on

Pa_data = Pa.read_ch1(100)  # value? data collection of Picoamp

Pm.set_data_collection(1)  # enable data collection of Powermeter
num = Pm.get_count()  # get number of collected data points
Pm_data = Pm.get_data(num)  # returns list with data points
