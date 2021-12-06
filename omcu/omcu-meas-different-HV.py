#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
#from submodules.Rotation import Rotation
from submodules.Laser import Laser
from submodules.Powermeter import Powermeter
from Occupancy import Occupancy
import time
import os
import numpy as np
import h5py

Ps = Picoscope()
#Psu0 = PSU(dev="/dev/PSU_0")
Psu1 = PSU(dev="/dev/PSU_1")
#Rot = Rotation()
L = Laser()
Pm = Powermeter()
oc = Occupancy()

# Psu settings
#Psu0.settings(1, voltage=12.0, current=3.0)  # psu for rotation stage
#Psu0.on()
#Rot.go_home()
#Psu0.off()
Psu1.settings(1, voltage=12.0, current=3.0)  # psu for PMT, Vcc
V0ctrl = 3.6  # HV_out = Vctrl*250
Psu1.settings(2, voltage=V0ctrl, current=0.1)  # psu for PMT, Vcontrol
#Psu1.on()
#time.sleep(1800)

Laser_temp = L.get_temp()
Pm.set_offset()  # set offset value when it's dark

# Laser settings depending on occupancy
L.on_pulsed()  # pulsed laser emission on
time.sleep(300)

threshold = -2

PMT = 'PMT-Hamamatsu-R15458-DM05949'
timestr = time.strftime("%Y%m%d-%H%M%S")
directory = 'data/' + PMT + '/' + timestr + '-withoutMolton-after5hoursintheDark-variableHV'
os.mkdir(directory)
suf = '.hdf5'
filename = PMT + '-variableHV-with-threshold' + str(threshold) + 'mV' + suf
filename_with_folder = directory + '/' + filename
h5 = h5py.File(filename_with_folder, 'w')

Vctrl = np.arange(3.6, 5.6, 0.4)
number0 = 10000
number = 100000
nSamples = Ps.get_nSamples()
t1 = time.time()
for V in Vctrl:
    Psu1.settings(2, voltage=V, current=0.1)
    HV = int(round(V*250))
    print('Vctrl =', V, 'HV =', HV)
    time.sleep(0.1)
    Laser_temp = L.get_temp()
    power = Pm.get_power()
    tune = 710
    L.set_tune_value(tune=tune)
    data_sgnl, _ = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number0)
    occ = oc.occ_data(data_sgnl, threshold)
    while occ < 0.02:
        tune = tune-5
        L.set_tune_value(tune=tune)
        data_sgnl, _ = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number0)
        occ = oc.occ_data(data_sgnl, threshold)
    while occ > 0.08:
        tune = tune+5
        L.set_tune_value(tune=tune)
        data_sgnl, _ = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number0)
        occ = oc.occ_data(data_sgnl, threshold)
    print('Laser tune value is', tune, '. Occupancy is', occ*100, '%')
    data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number)
    occ = oc.occ_data(data_sgnl, threshold)
    print('Measurement done. Occupancy is', occ*100, '%')

    data_sgnl_filt = []
    data_trg_filt = []
    for i, wf in enumerate(data_sgnl):
        minval = np.min(wf[:, 1])
        if minval < threshold:
            data_sgnl_filt.append(wf)
            data_trg_filt.append(data_trg[i])
    arr_sgnl = h5.create_dataset(f"HV{HV}/signal", (len(data_sgnl_filt), nSamples, 2), 'f')
    arr_trg = h5.create_dataset(f"HV{HV}/trigger", (len(data_trg_filt), nSamples, 2), 'f')
    arr_sgnl[:] = data_sgnl_filt
    arr_trg[:] = data_trg_filt

    arr_sgnl.attrs['Vctrl'] = f"{V}"
    arr_sgnl.attrs['HV'] = f"{HV}"
    arr_sgnl.attrs['Occupancy'] = f"{occ}"
    arr_sgnl.attrs['Position'] = 'Home'
    arr_sgnl.attrs['Powermeter'] = f"{power}"
    arr_sgnl.attrs['Laser temperature'] = f"{Laser_temp}"
    arr_trg.attrs['Laser temperature'] = f"{Laser_temp}"
    arr_sgnl.attrs['Laser tune value'] = f"{tune}"
    arr_trg.attrs['Laser tune value'] = f"{tune}"
    arr_sgnl.attrs['Units_voltage'] = 'mV'
    arr_sgnl.attrs['Units_time'] = 'ns'
    #TODO: mehr Attribute?
    time.sleep(0.1)

h5.close()
t2 = time.time()
deltaT = t2-t1
print(deltaT/60, 'min')

L.off_pulsed()
Psu1.off()