#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from devices.Picoscope import Picoscope
from devices.PSU import PSU
from devices.Rotation import Rotation
from devices.Laser import Laser
from devices.Powermeter import Powermeter
from util.Occupancy import Occupancy
import time
import os
import numpy as np
import h5py

Ps = Picoscope()
Psu0 = PSU(dev="/dev/PSU_0")
Psu1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()
L = Laser()
Pm = Powermeter()
oc = Occupancy()

# Psu settings
Psu0.settings(1, voltage=12.0, current=3.0)  # psu for rotation stage
Psu1.settings(1, voltage=5.0, current=0.1)  # psu for PMT, Vcc
Vctrl = 1.1
Psu1.settings(2, voltage=Vctrl, current=0.1)  # psu for PMT, Vcontrol
Psu0.on()
Rot.go_home()
Psu1.on()
time.sleep(3600)

Laser_temp = L.get_temp()
Pm.set_offset()  # set offset value when it's dark

PMT = 'PMT001'
#TODO: erstelle directory für PMT folder
timestr = time.strftime("%Y%m%d-%H%M%S")
directory = 'data/' + PMT + '/' + timestr
os.mkdir(directory)
suf = '.hdf5'
filename = PMT + suf
filename_with_folder = directory + '/' + filename
h5 = h5py.File(filename_with_folder, 'w')

# Laser settings depending on occupancy
L.on_pulsed()  # pulsed laser emission on
time.sleep(300)
f0 = 10e3
L.set_freq(f=f0)  # value?
tune = 710
L.set_tune_value(tune=tune)  # value?
number0 = 100000
threshold = -3
data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number0)
occ = oc.occ_data(data_sgnl, threshold)
while occ > 0.1:
    tune = tune+1
    L.set_tune_value(tune=tune)
    data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number0)
    occ = oc.occ_data(data_sgnl, threshold)
print('Laser tune value is', tune, '. Occupancy is', occ*100, '%')
#time.sleep(300)

delta_theta = 30  # 6
thetas = np.arange(0, 90.1, delta_theta)
#delta_phi = 15  # value?
#phis = np.arange(0, 360., delta_phi)
number = 100000
nSamples = Ps.get_nSamples()
t1 = time.time()
for i, theta in enumerate(thetas):  # rotation in xy plane
    Rot.set_theta(theta)
    n_phi_steps = 36 * np.sin(np.radians(theta))
    delta_phi = min(360 / n_phi_steps, 90)
    if theta==0:
        phis = [0]
    else:
        phis = np.arange(0, 360., delta_phi)
    for j, phi in enumerate(phis):  # rotation around PMT long axis
        Rot.set_phi(phi)
        pos = Rot.get_position()
        print(pos)
        time.sleep(0.1)
        Laser_temp = L.get_temp()
        power = Pm.get_power()
        data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=number)
        occ = oc.occ_data(data_sgnl, threshold)
        data_sgnl_filt = []
        data_trg_filt = []
        for i, wf in enumerate(data_sgnl):
            minval = np.min(wf[:, 1])
            if minval < threshold:
                data_sgnl_filt.append(wf)
                data_trg_filt.append(data_trg[i])
        arr_sgnl = h5.create_dataset(f"theta{theta}/phi{phi}/signal", (len(data_sgnl_filt), nSamples, 2), 'f')
        arr_trg = h5.create_dataset(f"theta{theta}/phi{phi}/trigger", (len(data_trg_filt), nSamples, 2), 'f')
        arr_sgnl[:] = data_sgnl_filt
        arr_trg[:] = data_trg_filt

        arr_sgnl.attrs['Vctrl'] = f"{Vctrl}"
        arr_trg.attrs['Vctrl'] = f"{Vctrl}"
        arr_sgnl.attrs['Occupancy'] = f"{occ}"
        arr_trg.attrs['Occupancy'] = f"{occ}"
        arr_sgnl.attrs['Powermeter'] = f"{power}"
        arr_trg.attrs['Powermeter'] = f"{power}"
        arr_sgnl.attrs['Laser temperature'] = f"{Laser_temp}"
        arr_trg.attrs['Laser temperature'] = f"{Laser_temp}"
        arr_sgnl.attrs['Units_voltage'] = 'mV'
        arr_trg.attrs['Units_voltage'] = 'mV'
        arr_sgnl.attrs['Units_time'] = 'ns'
        arr_trg.attrs['Units_time'] = 'ns'
        #TODO: mehr Attribute?
        time.sleep(0.1)
h5.close()
t2 = time.time()
deltaT = t2-t1
print(deltaT/60)

L.off_pulsed()
Rot.go_home()
Psu0.off()
Psu1.off()