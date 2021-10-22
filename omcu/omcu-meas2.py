#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Rotation import Rotation
from submodules.Picoamp import Picoamp
from submodules.Laser import Laser
from submodules.Powermeter import Powermeter
import time
import os
import numpy as np
import statistics as st

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
Vctrl = 1.1
Psu1.settings(2, voltage=Vctrl, current=0.1)  # psu for PMT, Vcontrol
Psu0.on()
Rot.go_home()
Psu1.on()

L.set_freq(f=1000000)  # value?
L.set_tune_value(tune=700)  # value?
L.on_pulsed()  # pulsed laser emission on

timestr = time.strftime("%Y%m%d-%H%M%S")
directory = 'data/' + timestr + '-' + str(Vctrl)
os.mkdir(directory)
delta_theta = 15  # 5
number_theta = int(90/delta_theta)
delta_phi = 90  # value?
number_phi = int(360/delta_phi)
# total_number = int(90/delta_theta * 360/delta_phi)
number = 1000
nSamples = Ps.get_nSamples()
data = np.zeros((number_theta, number_phi, 2, number, nSamples, 2))
Pm_data = np.zeros((number_theta, number_phi))
for i, theta in enumerate(range(0, 90, delta_theta)):  # rotation in xy plane
    Rot.set_theta(theta)
    for j, phi in enumerate(range(0, 360, delta_phi)):  # rotation around PMT long axis
        Rot.set_phi(phi)
        pos = Rot.get_position()
        time.sleep(0.1)
        Pm.set_data_collection(1)  # enable data collection of Powermeter
        num = Pm.get_count()  # get number of collected data points
        Pm_data_points = Pm.get_data(num)  # returns list with data points
        Pm_data_points_mean = st.mean(Pm_data_points)
        Pm_data[i][j] = Pm_data_points_mean
        # Pa_data = Pa.read_ch1(100)  # value? data collection of Picoamp
        data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000,
                                                   number=number)
        data[i][j][0] = data_sgnl
        data[i][j][1] = data_trg
        time.sleep(0.1)

filename_Ps = directory + '/' + timestr + '-' + str(number_theta) + '-' + str(number_phi) + '-' + str(number) + '.npy'
np.save(filename_Ps, data)
filename_Pm = directory + '/' + timestr + '-Powermeter-data' + '.npy'
np.save(filename_Pm, Pm_data)




