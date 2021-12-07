#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from Occupancy import Occupancy
import time
import os
import numpy as np
import h5py

Ps = Picoscope()
Psu1 = PSU(dev="/dev/PSU_1")
oc = Occupancy()

# Psu settings
Psu1.settings(1, voltage=12.0, current=3.0)  # psu for PMT, Vcc
V0ctrl = 3.6  # HV_out = Vctrl*250
Psu1.settings(2, voltage=V0ctrl, current=0.1)  # psu for PMT, Vcontrol
Psu1.on()
time.sleep(1800)

PMT = 'PMT-Hamamatsu-R15458-DM14218'
# os.mkdir('data/' + PMT)
timestr = time.strftime("%Y%m%d-%H%M%S")
directory = 'data/' + PMT + '/' + timestr + '-withoutTrigger-baseline'
os.mkdir(directory)
suf = '.hdf5'

filename = PMT + '-baseline' + suf
filename_with_folder = directory + '/' + filename
h5 = h5py.File(filename_with_folder, 'w')

Vctrl = np.arange(3.6, 5.6, 0.4)
number = 100000
nSamples = Ps.get_nSamples()
t1 = time.time()
for V in Vctrl:
    Psu1.settings(2, voltage=V, current=0.1)
    HV = int(round(V*250))
    print('Vctrl =', V, ', HV =', HV)
    time.sleep(0.1)
    data_sgnl = Ps.block_measurement_one_ch(channel=2, number=number)
    arr_sgnl = h5.create_dataset(f"HV{HV}/signal", (number, nSamples, 2), 'f')
    arr_sgnl[:] = data_sgnl

    arr_sgnl.attrs['Vctrl'] = f"{V}"
    arr_sgnl.attrs['HV'] = f"{HV}"
    arr_sgnl.attrs['Position'] = 'Home'
    arr_sgnl.attrs['Baseline'] = 'yes'
    arr_sgnl.attrs['Units_voltage'] = 'mV'
    arr_sgnl.attrs['Units_time'] = 'ns'
    Ps.stop_scope()
    time.sleep(0.1)

h5.close()
t2 = time.time()
deltaT = t2-t1
print(deltaT, 's')

Psu1.off()
