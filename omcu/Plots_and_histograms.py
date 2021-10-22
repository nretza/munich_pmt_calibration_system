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

    def get_info(self, filename='data/20211022-140412-1.1/20211022-140412-6-4-10.npy'):

        filename_split1 = filename.split('/')  # ['data', '20211022-140412-1.1', '20211022-140412-6-4-10.npy']
        folder_name = filename_split1[1]
        directory = 'data/' + folder_name
        filename_split2 = filename_split1[-1].split('-')  # ['20211020', '140412', '6', '4', '10.npy']
        filename_split3 = filename_split2[-1].split('.')  # ['10', 'npy']
        number = int(filename_split3[0])  # 10 = number of waveforms per measurement
        number_theta = int(filename_split2[2])  # 6
        number_phi = int(filename_split2[3])  # 4
        total_number = int(number_theta * number_phi)  # 24 = number of measurements
        total_number_waveforms = number * total_number  # 240

        return folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms

    def plot_waveforms(self, filename='data/20211022-140412-1.1/20211022-140412-6-4-10.npy'):

        data = np.load(filename)
        folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms =\
            self.get_info(filename)

        figname = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) + '-'\
                  + str(number) + '-Figure.pdf'

        plt.figure()
        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, total_number_waveforms)))
        for i, c in zip(data, colors):
            for j in i:
                for k in j[0]:
                    plt.plot(k[:, 0], k[:, 1], color=c)
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')

        plt.savefig(figname)
        plt.show()

    def plot_histogram_charge(self, filename='data/20211022-140412-1.1/20211022-140412-6-4-10.npy', nBins=20):

        data = np.load(filename)
        folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms =\
            self.get_info(filename)

        figname = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) + '-' \
                  + str(number) + '-Histogram.pdf'

        x_arr = []
        y_arr = []
        for i, n in enumerate(data):
            for j, m in enumerate(n):
                for k, p in enumerate(m[0]):
                    x = p[:, 0]
                    y = p[:, 1]
                    x_arr.append(x)
                    y_arr.append(y)

        areas = trapz(y_arr, x_arr, axis=1)

        plt.figure()
        plt.hist(areas, bins=nBins)
        plt.ylabel('counts')
        plt.xlabel('area [Vs]')

        plt.savefig(figname)
        plt.show()

        areas_name = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) + '-' \
                  + str(number) + '-areas.npy'
        np.save(areas_name, areas)
