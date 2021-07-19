#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Rotation import Rotation
from submodules.Picoamp import Picoamp
from submodules.Laser import Laser
from submodules.Powermeter import Powermeter
import time


Pico = Picoscope()
PSU0 = PSU(dev="/dev/PSU_0")
PSU1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()
Pamp = Picoamp()
L = Laser()
Pm = Powermeter()

time.sleep(300) # wait 5 minutes so that it's dark
Pm.set_offset()  # set offset value when it's dark
Pamp_data_dark = Pamp.read_ch1(100)  # value? data collection of Picoamp

PSU0.settings(channel=0, voltage=5.0, current=0.1)  # values?
PSU0.settings(channel=1, voltage=5.0, current=0.1)  # values?
PSU1.settings(channel=0, voltage=5.0, current=0.1)  # values?
PSU1.settings(channel=1, voltage=5.0, current=0.1)  # values?

L.set_freq(f=1000000)  # value?
L.set_tune_value(tune=20)  # value?
L.on_pulsed()  # pulsed laser emission on
Pamp_data = Pamp.read_ch1(100)  # value? data collection of Picoamp

Pm.set_data_collection(1)  # enable data collection of Powermeter
num = Pm.get_count()  # get number of collected data points
Pm_data = Pm.get_data(num)  # returns list with data points
