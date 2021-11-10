#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Rotation import Rotation
from Occupancy import Occupancy
import time
import os
import numpy as np
import h5py

Ps = Picoscope()
Psu0 = PSU(dev="/dev/PSU_0")
Psu1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()
oc = Occupancy()

# Psu settings
Psu0.settings(1, voltage=12.0, current=3.0)  # psu for rotation stage
Psu0.on()
Rot.go_home()
Psu0.off()
Psu1.settings(1, voltage=5.0, current=0.1)  # psu for PMT, Vcc
V0ctrl = 0.8
Psu1.settings(2, voltage=V0ctrl, current=0.1)  # psu for PMT, Vcontrol
Psu1.on()
time.sleep(1800)

PMT = 'PMT001'
#TODO: erstelle directory für PMT folder
timestr = time.strftime("%Y%m%d-%H%M%S")
directory = 'data/' + PMT + '/' + timestr
os.mkdir(directory)
suf = '.hdf5'
filename = PMT + suf
filename_with_folder = directory + '/' + filename
h5 = h5py.File(filename_with_folder, 'w')

threshold = -0.1
Vctrl = np.arange(0.8, 1.7, 0.1)
number = 1000
nSamples = Ps.get_nSamples()
t1 = time.time()
for V in Vctrl:
    Psu1.settings(2, voltage=V, current=0.1)
    print('Vctrl =', V)
    data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=threshold, number=number)
    occ = oc.occ_data(data_sgnl, threshold)
    arr_sgnl = h5.create_dataset(f"Vctrl{V}/signal", (number, nSamples, 2), 'f')
    arr_trg = h5.create_dataset(f"Vctrl{V}/trigger", (number, nSamples, 2), 'f')
    arr_sgnl[:] = data_sgnl
    arr_trg[:] = data_trg

    arr_sgnl.attrs['Vctrl'] = f"{V}"
    arr_trg.attrs['Vctrl'] = f"{V}"
    arr_sgnl.attrs['Occupancy'] = f"{occ}"
    arr_trg.attrs['Occupancy'] = f"{occ}"
    arr_sgnl.attrs['Position'] = 'Home'
    arr_trg.attrs['Position'] = 'Home'
    arr_sgnl.attrs['Baseline'] = 'yes'
    arr_trg.attrs['Baseline'] = 'yes'
    arr_sgnl.attrs['Units_voltage'] = 'mV'
    arr_trg.attrs['Units_voltage'] = 'mV'
    arr_sgnl.attrs['Units_time'] = 'ns'
    arr_trg.attrs['Units_time'] = 'ns'
    Ps.stop_scope()
    time.sleep(0.1)
h5.close()
t2 = time.time()
deltaT = t2-t1
print(deltaT/60)

Psu1.off()
