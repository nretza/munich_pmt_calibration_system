#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
import matplotlib.pyplot as plt
import numpy as np
from numpy import trapz
import os


class Plots:

    def __init__(self):

        Ps = Picoscope()
        self.nSamples = Ps.get_nSamples()

    def plot_waveforms(self, filename='data/20211022-140412-1.1/20211022-140412-6-4-10.npy'):

        data = np.load(filename)
        filename_split1 = filename.split('/')  # ['data', '20211022-140412-1.1', '20211022-140412-6-4-10.npy']
        filename_split2 = filename_split1[-1].split('-')  # ['20211020', '140412', '6', '4', '10.npy']
        filename_split3 = filename_split2[-1].split('.')  # ['10', 'npy']
        number = int(filename_split3[0])  # 10 = number of waveforms per measurement
        number_theta = int(filename_split2[2])  # 3
        number_phi = int(filename_split2[3])  # 4
        total_number = int(number_theta * number_phi)  # 12 = number of measurements
        total_number_waveforms = number * total_number  # 120
        nSamples = self.nSamples

        directory = 'data/plots/' + filename_split1[1]
        if not os.path.exists(directory):
            os.mkdir(directory)
        figname = directory + '/' + filename_split1[1] + '-' + str(number_theta) + '-' + str(number_phi) + '-'\
                  + str(number) + '-Figure.pdf'

        plt.figure()
        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, total_number_waveforms)))
        for i, n in enumerate(data):  # n0 = data[0][:]
            for j, m in n:  # m0 = n[0] = data[0][0][:]
                for k in m[0]:  # m[0]0 = m0[0] = data[0][0][0][:] = signal waveforms, m[1] would be trigger wfs
                    print(k) #plt.plot(k[:, 0], k[:, 1])
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')

        plt.savefig(figname)
        plt.show()