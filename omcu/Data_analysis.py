#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
import matplotlib.pyplot as plt
import numpy as np
import h5py
from Waveform import Waveform
import statistics as stat

#from Data_analysis import Analysis as Al
#data2910 = Al('./data/PMT001/20211029.../PMT001.hdf5')
#data2910.calculate_gain_sph(threshold)

class Analysis:

    def __init__(self, filename='./data/PMT001/20211028-114024/PMT001.hdf5'):
        self.filename = filename
        Ps = Picoscope()
        self.nSamples = Ps.get_nSamples()

    def calculate_gain_sph(self, threshold=-3):

        h5 = h5py.File(self.filename, 'r+')
        wfs = []
        for key in h5.keys():
            dataset = h5[key]['signal']
            for i, wf in enumerate(dataset):
                minval = np.min(wf[:,1])
                if minval < threshold:
                    wf_object = Waveform('theta0.0', 'phi0.0', dataset.attrs['Vctrl'], wf[:, 1], wf[:, 0])
                    wf_object.calculate_gain()
                    wfs.append(wf_object)

        return wfs

    def calculate_gain_sph_different_positions(self, threshold=-3):

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
        plt.subplot(2, 1, 1)
        plt.hist(gains,bins=nbins)
        plt.yscale('log')
        plt.ylabel('counts')
        plt.xlabel('gain')
        plt.show()

    def plot_wfs(self, wf_list):

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, len(wf_list))))
        plt.figure()
        for i, c in zip(wf_list, colors):
            plt.plot(i.x, i.y, color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

    def plot_gain_hv(self, wf_list):

        gains = []
        Vctrl = []
        HV = []
        data = {}
        for i in wf_list:
            gains.append(i.gain)
            v = "{:.1f}".format(float(i.Vctrl))
            Vctrl.append(v)
            hv = "{:.0f}".format(float(i.Vctrl) * 1e3)
            HV.append(hv)
            data.setdefault(hv, []).append(i.gain)

        means = {}
        for key in data.keys():
            mean = stat.mean(data[key])
            means.setdefault(key, []).append(mean)

        plt.figure()
        plt.subplot(2, 1, 1)
        for key in means.keys():
            if key == '0':
                pass
            else:
                plt.plot(key, means[key], '.', color='blue')
        plt.yscale('log')
        plt.ylabel('gain')
        plt.xlabel('HV [V]')
        plt.show()

        return means

