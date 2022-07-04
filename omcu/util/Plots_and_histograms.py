#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>


import matplotlib.pyplot as plt
import numpy as np
import scipy.constants as const

from numpy import trapz

from omcu.devices.Picoscope import Picoscope

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
        number_theta = int(filename_split2[-3])  # 6
        number_phi = int(filename_split2[-2])  # 4
        total_number = int(number_theta * number_phi)  # 24 = number of measurements
        total_number_waveforms = number * total_number  # 240

        return folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms

    def filter_sph_and_set_data_to_SI(self, filename='data/20211026-101255-1.1/20211026-101255-1.1-3-2-1000.npy',
                                      threshold=-4):

        data = np.load(filename)
        x_arr = []
        y_arr = []
        for i, n in enumerate(data[:, :, 0, :]):  # in all waveforms
            for m in n:
                for j, y in enumerate(m):
                    minval = np.min(y)
                    if minval < threshold:
                        x_arr.append(m[j][:, 0] * 1e-9)
                        y_arr.append(m[j][:, 1] * 1e-3)

        return x_arr, y_arr

    def plot_waveforms(self, filename='data/20211022-140412-1.1/20211022-140412-6-4-10.npy'):

        data = np.load(filename)
        folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms =\
            self.get_info(filename)

        figname = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) + '-'\
                  + str(number) + '-Figure.pdf'

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, total_number_waveforms)))
        plt.figure()
        for i, c in zip(data, colors):
            for j in i:
                for k in j[0]:
                    plt.plot(k[:, 0], k[:, 1], color=c)
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')

        plt.savefig(figname)
        plt.show()

    def plot_sph_waveforms(self, filename='data/20211026-101255-1.1/20211026-101255-1.1-3-2-1000.npy', threshold=-4):

        folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms =\
            self.get_info(filename)

        figname = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) + '-'\
                  + str(number) + '-Figure-sph.pdf'

        x_arr, y_arr = self.filter_sph_and_set_data_to_SI(filename, threshold)

        number_new=len(y_arr)
        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, number_new)))
        plt.figure()
        for x, y, c in zip(x_arr, y_arr, colors):
            plt.plot(x, y, color=c)
            plt.xlabel('Time (s)')
            plt.ylabel('Voltage (V)')
        plt.savefig(figname)
        plt.show()

    def calculate_areas(self, filename='data/20211026-101255-1.1/20211026-101255-1.1-3-2-1000.npy', threshold=-4):

        folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms =\
            self.get_info(filename)

        x_arr, y_arr = self.filter_sph_and_set_data_to_SI(filename, threshold)

        areas = trapz(y_arr, x_arr, axis=1)

        areas_name = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) + '-' \
                  + str(number) + '-areas.txt'
        np.savetxt(areas_name, areas)

        return areas

    def calculate_nr_electrons(self, filename='data/20211026-101255-1.1/20211026-101255-1.1-3-2-1000.npy', threshold=-4):

        folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms =\
            self.get_info(filename)

        areas = self.calculate_areas(filename, threshold)

        e = const.e
        number_of_electrons = []
        for i in areas:
            No = abs(i/e)
            number_of_electrons.append(No)

        number_of_electrons_name = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) +\
                                   '-' + str(number) + '-number_of_electrons.txt'
        np.savetxt(number_of_electrons_name, number_of_electrons)

        for i in number_of_electrons:
            max = np.max(i)

        return max

    def plot_histogram_charge(self, filename='data/20211026-101255-1.1/20211026-101255-1.1-3-2-1000.npy', threshold=-4,
                              nBins=30):

        folder_name, directory, number, number_theta, number_phi, total_number, total_number_waveforms =\
            self.get_info(filename)

        figname = directory + '/' + folder_name + '-' + str(number_theta) + '-' + str(number_phi) + '-' \
                  + str(number) + '-Histogram.pdf'

        areas = self.calculate_areas(filename, threshold)

        plt.figure()
        plt.hist(areas, bins=nBins)
        plt.ylabel('counts')
        plt.xlabel('area [Vs]')
        #TODO: Gauß fit
        plt.savefig(figname)
        plt.show()
