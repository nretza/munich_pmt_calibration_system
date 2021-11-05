#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
import matplotlib.pyplot as plt
import numpy as np
import h5py
from Waveform import Waveform

#from Data_analysis import Analysis as Al
#data2910 = Al('./data/PMT001/20211029.../PMT001.hdf5')
#data2910.calculate_gain_sph(threshold)

class Analysis:

    def __init__(self, filename='./data/PMT001/20211028-114024/PMT001.hdf5'):
        self.filename = filename
        Ps = Picoscope()
        self.nSamples = Ps.get_nSamples()

    def calculate_gain_sph(self, threshold=-4):

        h5 = h5py.File(self.filename, 'r+')
        wfs = []
        for key in h5.keys():
            for key2 in h5[key]:
                dataset = h5[key][key2]['signal']
                for i, wf in enumerate(dataset):
                    minval = np.min(wf[:,1])
                    if minval < threshold:
                        wf_object = Waveform(key, key2, dataset.attrs['Vctrl'], wf[:, 1], wf[:, 0])
                        wf_object.calculate_gain()
                        wfs.append(wf_object)

        return wfs

    def plot_hist_gain(self, wf_list, nbins=100):

        gains = []
        for i in wf_list:
            gains.append(i.gain)

        plt.figure()
        plt.hist(gains,bins=nbins)
        plt.ylabel('counts')
        plt.xlabel('gain')
        plt.show()

    def plot_wfs(self, wf_list):

        x = []
        y = []

        for i in wf_list:
            x.append(i.x)
            y.append(i.y)

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, len(x))))
        plt.figure()
        for i, j, c in zip(x, y, colors):
            plt.plot(i, j, color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

    def plot_gain_hv(self, wf_list):

        gains = []
        Vctrl = []
        for i in wf_list:
            gains.append(i.gain)
            Vctrl.append(i.Vctrl)

        plt.figure()
        plt.plot(Vctrl, gains)
        plt.show()

