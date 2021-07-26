#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Laser import Laser
#from submodules.Rotation import Rotation
#from submodules.Picoamp import Picoamp
import matplotlib.pyplot as plt

P = Picoscope()
#PSU0 = PSU(dev="/dev/PSU_0")
PSU1 = PSU(dev="/dev/PSU_1")
#Rot = Rotation()
#Pamp = Picoamp()
L=Laser()

#PSU0.settings(channel=1, voltage=5.0, current=0.1)  # values?
#PSU0.settings(channel=2, voltage=5.0, current=0.1)  # values?
#PSU1.settings(channel=1, voltage=5.0, current=0.1)  # values?
#PSU1.settings(channel=2, voltage=1.1, current=0.1)  # values?
PSU1.on()
L.on_pulsed()
file1, data1=P.block_measurement(channel=0, trgchannel=0, direction=2, threshold=-100, bufchannel=0, number=1)
file2, data2=P.block_measurement(channel=2, trgchannel=2, direction=2, threshold=4500, bufchannel=2, number=1)

x1=data1[0,:,0]
y1=data1[0,:,1]
plt.plot(x1,y1)
plt.show()

x2=data2[0,:,0]
y2=data2[0,:,1]
plt.plot(x2,y2)
plt.show()

#Rot.go_home()  # or Rot.set_position(phi, theta), values?
#Pamp_data = Pamp.read_ch1(100)  # value? data collection of Picoamp


#Pico.block_measurement()  # values?