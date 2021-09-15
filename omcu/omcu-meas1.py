#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Laser import Laser
from submodules.Rotation import Rotation
import matplotlib.pyplot as plt
import time

ps = Picoscope()
psu0 = PSU(dev="/dev/PSU_0")
psu1 = PSU(dev="/dev/PSU_1")
rot = Rotation()
L=Laser()

psu0.settings(1, voltage=12.0, current=3.0)
psu1.settings(1, voltage=5.0, current=0.1)
psu1.settings(2, voltage=1.1, current=0.1)
psu0.on()
psu1.on()
L.on_pulsed()


filename1, filename2, data_sgnl, data_trg, deltaT = ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=100)

for i in range(0, 50, 1):
    rot.set_theta(i)
    time.sleep(1)

psu0.off()
psu1.off()
L.off_pulsed()

ps.plot_data(filename1)
ps.plot_histogram(filename1, nBins=10)



#rot.go_home()  # or Rot.set_position(phi, theta), values?