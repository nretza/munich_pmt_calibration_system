#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Laser import Laser
from submodules.Rotation import Rotation
import time


Ps = Picoscope()
PSU0 = PSU(dev="/dev/PSU_0")
PSU1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()
L = Laser()

PSU0.settings(1, voltage=12.0, current=3.0)
PSU1.settings(1, voltage=5.0, current=0.1)
PSU1.settings(2, voltage=1.1, current=0.1)
PSU0.on()
PSU1.on()
L.on_pulsed()


data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=100)

for i in range(0, 50, 1):
    Rot.set_theta(i)
    time.sleep(1)

PSU0.off()
PSU1.off()
L.off_pulsed()





#rot.go_home()  # or Rot.set_position(phi, theta), values?