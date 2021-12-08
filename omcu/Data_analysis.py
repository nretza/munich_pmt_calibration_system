#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import matplotlib.pyplot as plt
import numpy as np
import h5py
from Waveform import Waveform
import statistics as stat
from scipy.signal import find_peaks


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
            if nr_entries <= 1000:
                nbins = int(nr_entries/50)
            else:
                nbins = int(nr_entries/100)

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
            if nr_entries <= 1000:
                nbins = int(nr_entries/50)
            else:
                nbins = int(nr_entries/100)

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

    def plot_wfs(self, wf_list, threshold=-2):

        data = {}
        for i in wf_list:
            data.setdefault(int(i.HV), []).append(i)
        data2 = {}
        for i in sorted(data):
            data2[i] = data[i]

        cmap = plt.cm.viridis
        for key in data2:
            colors = iter(cmap(np.linspace(0, 0.7, 10)))
            plt.figure()
            for i in range(10):
                for wf, c in zip(data2[key], colors):
                    if wf.min < threshold:
                        plt.plot(wf.x, wf.y, color=c)

            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.title(f"Waveforms for HV={key}V")
            figname = self.filename + '-waveforms-at-' + str(key) + 'V-threshold' + str(threshold) + 'mV.pdf'
            plt.savefig(figname)
            plt.show()

    def plot_wfs_mask(self, wf_list, threshold=-2):

        data = {}
        for i in wf_list:
            data.setdefault(int(i.HV), []).append(i)
        data2 = {}
        for i in sorted(data):
            data2[i] = data[i]

        cmap = plt.cm.viridis
        for key in data2:
            colors = iter(cmap(np.linspace(0, 0.7, 10)))
            plt.figure()
            for i in range(10):
                for wf, c in zip(data2[key], colors):
                    if wf.min < threshold:
                        plt.plot(wf.x[wf.mask], wf.y[wf.mask], color=c)

            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.title(f"Waveforms for HV={key}V")
            figname = self.filename + '-waveforms-at-' + str(key) + 'V-mask-threshold' + str(threshold) + 'mV.pdf'
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
            return np.exp(a) * np.exp(b * x)

        plt.figure()
        plt.subplot(2, 1, 1)
        plt.plot(x, y, 'yo', label="Data")
        plt.plot(x, fit_fn(x, a, b), '--k', label="Fitted Curve")
        plt.legend()
        plt.yscale('log')
        plt.ylabel('Gain')
        plt.xlabel('HV [V]')

        # plt.title(f"Gain of PMT <name>")
        figname = self.filename + '-gain-hv-threshold' + str(threshold) + '.pdf'
        plt.savefig(figname)
        plt.show()

        for key in means:
            print(key, 'V:', 'gain =', float(means[key]) / 1e7, '10^7')

        xx = np.linspace(500, 2500, 100000)
        yy = fit_fn(xx, a, b)
        hvs = {}
        for key in [1e6, 5e6, 1e7]:
            hvs[key] = xx[np.argmin(np.abs(yy - key))]
            print('HV for gain = ', key / 1e6, '1e6', 'is', hvs[key])
        hvs_arr = list(hvs.items())
        filename = self.filename + '-gain-hv-threshold' + str(threshold) + '.txt'
        np.savetxt(filename, hvs_arr, header='gain HV [V]')

        return means

    def get_dark_rate(self, wf_list, threshold=-2, width=3):

        T = wf_list[0].x[-1]*1e-9
        nHV = 5
        n = len(wf_list)/nHV

        peaks_dic = {}
        no_peaks_dic = {}
        for i, wf in enumerate(wf_list):
            peaks = find_peaks(-wf.y, height=-threshold, width=width)
            if len(peaks[0]) > 0:
                dic = {}
                dic.setdefault(i, []).append(peaks)
                dic.setdefault(i, []).append(wf)
                peaks_dic.setdefault(wf.HV, []).append(dic)
            else:
                no_peaks_dic.setdefault(wf.HV, []).append(wf)

        peaks_dic2 = {}
        for i in sorted(peaks_dic):
            peaks_dic2[i] = peaks_dic[i]
        no_peaks_dic2 = {}
        for i in sorted(no_peaks_dic):
            no_peaks_dic2[i] = no_peaks_dic[i]

        dark_rate = {}
        for key in peaks_dic2:
            count = 0
            widths = 0.0
            for i, peak in enumerate(peaks_dic2[key]):
                for key2 in peaks_dic2[key][i]:
                    l = len(peaks_dic2[key][i][key2][0][0])
                    count += l
                    for w in peaks_dic2[key][i][key2][0][1]['widths']:
                        widths += w
            time = (T * n - widths * 1e-9)
            rate = count/time
            print(key, n, count, time, rate)
            dark_rate[key] = rate
        dark_rate_arr = list(dark_rate.items())
        filename = self.filename + '-dark-rate-threshold' + str(threshold) + 'mV-width' + str(width) + 'ns.txt'
        fmt = '%d', '%1.9f'
        np.savetxt(filename, dark_rate_arr, header='HV [V], dark rate [Hz]', fmt=fmt)

        return peaks_dic, no_peaks_dic

    def plot_peaks(self, peaks_dic, threshold=-2, width=3):

        for key in peaks_dic:
            plt.figure()
            for i in range(5):
                for j in peaks_dic[key][i]:
                    plt.plot(peaks_dic[key][i][j][-1].x, peaks_dic[key][i][j][-1].y, 'green')  # or also color bar?
                    for k in peaks_dic[key][i][j][0][0]:
                        plt.plot(peaks_dic[key][i][j][-1].x[k], peaks_dic[key][i][j][-1].y[k], 'yo')
            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.title(f"Waveforms for HV={key}V")
            plt.axhline(y=threshold, color='red', linestyle='--')
            plt.show()

            figname = self.filename + '-waveforms-peaks-threshold' + str(threshold) + 'mV-width' + str(width) + '.pdf'
            plt.savefig(figname)
            plt.show()
