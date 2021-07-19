#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Rotation import Rotation


Pico = Picoscope()
PSU0 = PSU(dev="/dev/PSU_0")
PSU1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()

PSU0.settings(channel=0, voltage=5.0, current=0.1)  # values?
PSU0.settings(channel=1, voltage=5.0, current=0.1)  # values?
PSU1.settings(channel=0, voltage=5.0, current=0.1)  # values?
PSU1.settings(channel=1, voltage=5.0, current=0.1)  # values?

Rot.go_home()  # or Rot.set_position(phi, theta), values?
Pico.block_measurement()  # values?