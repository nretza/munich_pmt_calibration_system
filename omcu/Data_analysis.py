#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import matplotlib.pyplot as plt
import numpy as np
import h5py
from Waveform import Waveform
import statistics as stat


# from Data_analysis import Analysis as Al
# data2910 = Al('./data/PMT001/20211029.../PMT001.hdf5')
# data2910.calculate_gain_sph(threshold)

class Analysis:

    def __init__(self, filename):
        self.filename = filename

    def get_baseline_mean(self):

        h5 = h5py.File(self.filename, 'r+')
        wfs = []
        for key in h5.keys():
            dataset = h5[key]['signal']
            for i, wf in enumerate(dataset):
                HV = int(dataset.attrs['HV'])
                wf_object = Waveform('theta0.0', 'phi0.0', HV, wf[:, 0], wf[:, 1], np.min(wf[:, 1]))
                wf_object.mean()
                wfs.append(wf_object)

        means = []
        for i in wfs:
            means.append(i.mean)

        total_mean = np.mean(means)
        std = np.std(means)

        return total_mean, std

    def get_wfs(self, baseline=0.1):

        h5 = h5py.File(self.filename, 'r+')
        wfs = []
        for key in h5.keys():
            dataset = h5[key]['signal']
            for i, wf in enumerate(dataset):
                y_corr = wf[:, 1] - baseline
                minval = np.min(y_corr)
                HV = int(dataset.attrs['HV'])
                wf_object = Waveform('theta0.0', 'phi0.0', HV, wf[:, 0], y_corr, minval)
                wf_object.calculate_gain()
                wfs.append(wf_object)
        h5.close()

        return wfs

    def get_wfs_different_positions(self, baseline=0.1):

        h5 = h5py.File(self.filename, 'r+')
        wfs = []
        for key in h5.keys():
            for key2 in h5[key]:
                dataset = h5[key][key2]['signal']
                for i, wf in enumerate(dataset):
                    y_corr = wf[:, 1] - baseline
                    minval = np.min(wf[:, 1])
                    HV = int(dataset.attrs['HV'])
                    wf_object = Waveform(key, key2, HV, wf[:, 0], y_corr, minval)
                    wf_object.calculate_gain()
                    wfs.append(wf_object)
        h5.close()

        return wfs

    def plot_hist_ampl(self, wf_list):

        amplitudes = {}
        for i in wf_list:
            amplitudes.setdefault(int(i.HV), []).append(i.min)
        amplitudes2 = {}
        for i in sorted(amplitudes):
            amplitudes2[i] = amplitudes[i]

        for key in amplitudes2:
            nr_entries = len(amplitudes2[key])
            nbins = int(nr_entries / 100)

            plt.figure()
            plt.subplot(2, 1, 1)

            y, x, _ = plt.hist(amplitudes2[key], bins=nbins)
            plt.yscale('log')
            plt.ylabel('Counts')
            plt.xlabel('Amplitude [mV]')
            plt.title(f"Amplitude Histogram for HV={key}V")
            figname = self.filename + '-hist-ampl-' + str(key) + 'V.pdf'
            plt.savefig(figname)
            plt.show()
            print('Maximum at x=', x[np.where(y == y.max())])
            print('Number of entries', nr_entries, ', Number of bins:', nbins)

        return amplitudes2

    def plot_hist_gain(self, wf_list, threshold=-2):

        gains = {}
        for i in wf_list:
            if i.min < threshold:
                gains.setdefault(int(i.HV), []).append(i.gain)
        gains2 = {}
        for i in sorted(gains):
            gains2[i] = gains[i]

        for key in gains2:
            nr_entries = len(gains2[key])
            nbins = int(nr_entries / 100)

            plt.figure()
            plt.subplot(2, 1, 1)
            y, x, _ = plt.hist(gains2[key], bins=nbins)
            plt.yscale('log')
            plt.ylabel('Counts')
            plt.xlabel('Gain')
            plt.ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
            plt.title(f"Gain Histogram for HV={key}V")
            figname = self.filename + '-hist-gain-' + str(key) + 'V-threshold' + str(threshold) + 'mV.pdf'
            plt.savefig(figname)
            plt.show()
            print('Number of entries', nr_entries, ', Number of bins:', nbins)

    def plot_wfs(self, wf_list, threshold=-2):  # todo: select HV

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, len(wf_list))))
        plt.figure()
        for i, c in zip(wf_list, colors):
            if i.min < threshold:
                plt.plot(i.x, i.y, color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        figname = self.filename + '-waveforms-threshold' + str(threshold) + 'mV.pdf'
        plt.savefig(figname)
        plt.show()

    def plot_wfs_mask(self, wf_list, threshold=-2):  # todo: select HV

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, len(wf_list))))
        plt.figure()
        for i, c in zip(wf_list, colors):
            if i.min < threshold:
                plt.plot(i.x[i.mask], i.y[i.mask], color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        figname = self.filename + '-waveforms-mask-threshold' + str(threshold) + 'mV.pdf'
        plt.savefig(figname)
        plt.show()

    def plot_gain_hv(self, wf_list, threshold=-2):

        data = {}
        for i in wf_list:
            if i.min < threshold:
                data.setdefault(int(i.HV), []).append(i.gain)
        data2 = {}
        for i in sorted(data):
            data2[i] = data[i]

        means = {}
        for key in data2.keys():
            means[key] = stat.mean(data2[key])

        x = list(means.keys())
        y = list(means.values())

        x = np.array(x, dtype=float)
        y = np.array(y, dtype=float)

        p, V = np.polyfit(x, np.log(y), 1, w=np.sqrt(y), cov=True)
        b = p[0]
        a = p[1]
        print('a =', a, 'with var =', V[0][0])
        print('b =', b, 'with var =', V[1][1])
        print('fit curve: y = exp(a) * exp(b*x)')

        def fit_fn(x, a, b):
            return np.exp(a) * np.exp(b * i)

        fit = []
        for i in x:
            fit.append(fit_fn(x, a, b))

        plt.figure()
        plt.subplot(2, 1, 1)
        plt.plot(x, y, 'yo', label="Data")
        plt.plot(x, fit, '--k', label="Fitted Curve")
        plt.legend()
        plt.yscale('log')
        plt.ylabel('gain')
        plt.xlabel('HV [V]')
        #plt.title(f"Gain of PMT-Hamamatsu-R15458-DM14218")
        #figname = self.filename + '-gain-hv-threshold' + str(threshold) + '.pdf'
        #plt.savefig(figname)
        plt.show()

        for key in means:
            print(key, 'V:', 'gain =', float(means[key]) / 1e7, '10^7')


        return means

