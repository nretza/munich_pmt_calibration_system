#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Rotation import Rotation
from submodules.Laser import Laser
from submodules.Picoamp import Picoamp
from submodules.Powermeter import Powermeter
from Occupancy import Occupancy
from Plots_and_histograms import Plots
import time
import os
import numpy as np
import h5py

PMT = 'PMT001'
#TODO: erstelle directory für PMT folder
timestr = time.strftime("%Y%m%d-%H%M%S")
directory = 'data/' + PMT + '/' + timestr
os.mkdir(directory)
suf = '.hdf5'
filename = PMT + suf
filename_with_folder = directory + '/' + filename

Ps = Picoscope()
Psu0 = PSU(dev="/dev/PSU_0")
Psu1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()
L = Laser()
Pm = Powermeter()
#Pa = Picoamp()
oc = Occupancy()
pl = Plots()

time.sleep(300)  # wait 5 minutes so that it's dark
Pm.set_offset()  # set offset value when it's dark
#Pa_data_dark = Pa.read_ch1(100)  # value? data collection of Picoamp

# turn on laser for it to heat up
L.on_pulsed()  # pulsed laser emission on
time.sleep(1800)  # wait 30 minutes
power0 = Pm.get_power()
print('Powermeter:', power0, 'W')

# Psu settings
Psu0.settings(1, voltage=12.0, current=3.0)  # psu for rotation stage
Psu1.settings(1, voltage=5.0, current=0.1)  # psu for PMT, Vcc
Vctrl = 1.1
Psu1.settings(2, voltage=Vctrl, current=0.1)  # psu for PMT, Vcontrol
Psu0.on()
Rot.go_home()
Psu1.on()

# Laser settings depending on occupancy
f0 = 10e3
L.set_freq(f=f0)  # value?
tune = 710
L.set_tune_value(tune=tune)  # value?
number0 = 10000
data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number0)
occ = oc.occ_data(data_sgnl, -4)
while occ > 0.1:
    tune = tune+1
    L.set_tune_value(tune=tune)
    data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number0)
    occ = oc.occ_data(data_sgnl, -4)
print('Laser tune value is', tune, '. Occupancy is', occ*0.01, '%')
time.sleep(300)

delta_theta = 15  # 5
thetas = np.arange(0, 90.1, delta_theta)
delta_phi = 15  # value?
phis = np.arange(0, 360., delta_phi)
number = 1000
nSamples = Ps.get_nSamples()
t1 = time.time()
for i, theta in enumerate(thetas):  # rotation in xy plane
    Rot.set_theta(theta)
    for j, phi in enumerate(phis):  # rotation around PMT long axis
        Rot.set_phi(phi)
        pos = Rot.get_position()
        print(pos)
        time.sleep(0.1)
        power = Pm.get_power()
        # Pa_data = Pa.read_ch1(100)  # value? data collection of Picoamp
        with h5py.File(filename_with_folder, 'w') as f:
            g = f.create_group(str(theta))
            gg = g.create_group(str(phi))
            data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000,
                                                         number=number)
            arr_sgnl = gg.create_dataset('signal', data=data_sgnl)
            arr_trg = gg.create_dataset('trigger', data=data_trg)

            arr_sgnl.attrs['Vctrl'], arr_trg.attrs['Vctrl'] = Vctrl
            arr_sgnl.attrs['Powermeter'], arr_trg.attrs['Powermeter'] = power
            arr_sgnl.attrs['Units_voltage'], arr_trg.attrs['Units_voltage'] = 'mV'
            arr_sgnl.attrs['Units_time'], arr_trg.attrs['Units_time'] = 'ns'
            #TODO: mehr Attribute?
            f.close()
            time.sleep(0.1)
t2 = time.time()
deltaT = t2-t1
print(deltaT)

L.off_pulsed()
Rot.go_home()
Psu0.off()
Psu1.off()