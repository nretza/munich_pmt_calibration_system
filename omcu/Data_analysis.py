#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import matplotlib.pyplot as plt
import numpy as np
import h5py
import math

from scipy import optimize
from scipy.signal import find_peaks
from scipy.signal import argrelextrema
from scipy.interpolate import UnivariateSpline as US
import scipy.constants as const

from util import Waveform

class Analysis:

    def __init__(self, filename):
        self.filename = filename
        self.loadData()
    
    def loadData(self, source='signal'):
        h5 = h5py.File(self.filename, 'r')
        HVs = h5.keys()
        self.wfDic = {}
        for key in HVs:
            dataset = h5[key][source]
            wfList = []
            HV = int(key[2:])
            for i, wf in enumerate(dataset):
                wf_object = Waveform('theta0.0', 'phi0.0', HV, wf[:, 0], wf[:, 1], np.min(wf[:, 1]))
                wf_object.mean()
                wf_object.calculate_gain()
                wfList.append(wf_object)
            self.wfDic[str(HV)] = wfList
        h5.close()

    def loadData_part(self, source='signal'):
        h5 = h5py.File(self.filename, 'r')
        HVs = h5.keys()
        self.wfDic = {}
        for key in HVs:
            dataset = h5[key][source][:10000]
            wfList = []
            HV = int(key[2:])
            for i, wf in enumerate(dataset):
                wf_object = Waveform('theta0.0', 'phi0.0', HV, wf[:, 0], wf[:, 1], np.min(wf[:, 1]))
                wf_object.mean()
                wf_object.calculate_gain()
                wfList.append(wf_object)
            self.wfDic[str(HV)] = wfList
        h5.close()

    def get_baseline_mean(self):
        if not hasattr(self, 'wfDic'):
            self.loadData

        self.HVmeans = {}
        for key, values in self.wfDic.items():
            means = [wf.mean for wf in values]
            self.HVmeans[key] = (np.mean(means), np.std(means))
        return self.HVmeans
    
    def subtractBaseline(self, baselineDict=None):
        if baselineDict == None:
            baselineDict = self.HVmeans
        for (key, wfs), (baselineKey, mean) in zip(self.wfDic.items(), baselineDict.items()):
            if baselineKey == key:
                for wf in wfs:
                    wf.subtractBaseline(mean[0])

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

    def plot_wfs(self, number=10, threshold=-2):

        cmap = plt.cm.viridis
        for key in self.wfDic:
            colors = iter(cmap(np.linspace(0, 0.7, 10)))
            plt.figure()
            for i in range(number):
                for wf, c in zip(self.wfDic[key], colors):
                    if wf.min < threshold:
                        plt.plot(wf.x, wf.y, color=c)

            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.title(f"Waveforms for HV={key}V")
            figname = self.filename[:-5] + '-waveforms-at-' + str(key) + 'V-threshold' + str(np.round(threshold,2)) + 'mV.pdf'
            plt.savefig(figname)
            plt.show()

    def plot_wfs_mask(self, number=10, threshold=-2):

        cmap = plt.cm.viridis
        for key in self.wfDic:
            colors = iter(cmap(np.linspace(0, 0.7, 10)))
            plt.figure()
            for i in range(number):
                for wf, c in zip(self.wfDic[key], colors):
                    if wf.min < threshold:
                        plt.plot(wf.x[wf.mask], wf.y[wf.mask], color=c)

            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.title(f"Waveforms for HV={key}V")
            figname = self.filename[:-5] + '-waveforms-at-' + str(key) + 'V-mask-threshold' + str(np.round(threshold,2)) + 'mV.pdf'
            plt.savefig(figname)
            plt.show()

    def overallSPE(self):
        self.overallWF = {}
        self.mask = {}
        for key, values in self.wfDic.items():
            xValues = np.array([val.x for val in values])
            overallX = np.mean(xValues, axis=0)
            yValues = np.array([val.y for val in values])
            overallY = np.mean(yValues, axis=0)
            indMin = np.argmin(overallY)
            xlim1 = overallX[indMin-10]
            xlim2 = overallX[indMin+15]
            self.mask[key] = (overallX >= xlim1) & (overallX <= xlim2)
            self.overallWF[key] = (overallX, overallY)

    def plot_overallSPE(self):
        for key, value in self.overallWF.items():
            plt.figure()
            plt.plot(value[0], value[1])
            plt.xlabel('Time [ns]')
            plt.ylabel('Voltage [mV]')
            plt.title(f"Average waveform for HV={key}V")
            figname = self.filename[:-5] + '-average-waveform-at-' + str(key) + 'V.pdf'
            plt.savefig(figname)
            plt.show()

    def plot_overallSPE_all(self, name):

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, len(self.overallWF))))
        plt.figure()
        for (key, value), c in zip(self.overallWF.items(), colors):
            plt.plot(value[0][200:300], value[1][200:300], color=c, label='HV='+str(key)+'V')
        plt.xlabel('Time [ns]')
        plt.ylabel('Voltage [mV]')
        plt.legend(loc='lower left', fontsize=8)
        plt.title('PMT '+name)
        figname = self.filename[:-5] + '-average-waveforms.pdf'
        plt.savefig(figname)
        plt.show()

    def plot_overallSPE_mask(self):
        for key, value in self.overallWF.items():
            plt.figure()
            plt.plot(value[0][self.mask[key]], value[1][self.mask[key]])
            plt.xlabel('Time [ns]')
            plt.ylabel('Voltage [mV]')
            plt.title(f"Average waveform for HV={key}V")
            figname = self.filename[:-5] + '-average-waveform-at-' + str(key) + 'V-mask.pdf'
            plt.savefig(figname)
            plt.show()

    def plot_hist_ampl(self, excl=['900', '1300']):

        amplitudes = {}
        for key in self.wfDic:
            if key not in excl:
                data = []
                for wf in self.wfDic[key]:
                    data.append(wf.min)

                nr_entries = len(self.wfDic[key])
                nbins = int(nr_entries / 100)

                entries, edges = np.histogram(data, bins=nbins)
                bin_m = (edges[:-1] + edges[1:]) / 2

                x = bin_m
                y = entries

                # Maxima = argrelextrema(y, np.greater, order=3)[0]
                # if len(Maxima) >= 2:
                #     if x[Maxima[-1]] > -1:
                #         indMax = Maxima[-2]
                #     else:
                #         indMax = Maxima[-1]
                # else:
                #     indMax = Maxima[0]
                # yMax = y[indMax]
                # Minima = argrelextrema(y, np.less, order=1)[0]
                #
                # splitInd = 0
                # for i in Minima[Minima > indMax]:
                #     prozent = y[i] / yMax
                #     if prozent <= 0.25:
                #         splitInd = i
                #         break
                # if splitInd == 0:
                #     splitInd = indMax + 4
                #
                # mask = np.arange(splitInd + 1)
                #
                # def gaussian(x, a, mu, sigma):
                #     return a * np.exp(- (x - mu) ** 2 / (sigma ** 2))
                #
                # a0 = yMax
                # mu0 = x[indMax]
                #
                # x_halb = x[int(np.argmax(y) / 2)]
                # x_ymax = x[np.argmax(y)]
                # sigma0 = 2 * abs(x_halb + x_ymax)
                #
                # xfit = np.linspace(np.min(x), np.max(x), 100)
                # popt, pcov = optimize.curve_fit(gaussian, x[mask], y[mask], p0=(a0, mu0, sigma0), maxfev=int(1e4))
                #
                # amplMean = popt[1]
                # amplitudes[key] = amplMean
                #
                # mask2 = gaussian(xfit, *popt) > 0

                fig, ax1 = plt.subplots()
                ax1.hist(data, bins=nbins, histtype='step', log=True, linewidth=2.0)
                #ax1.vlines(x[splitInd], 0, np.max(y) + 100, 'orange', linewidth=2.0, label='fit cutoff')
                #ax1.plot(xfit[mask2], gaussian(xfit, *popt)[mask2], color='black', linewidth=2.0,
                         #label=r'$\mu$=' + str(np.round(popt[1], 3)) + '\n$\sigma$=' + str(np.round(popt[2], 3)))
                ax1.set_xlabel('Amplitude [mV]')
                ax1.set_ylabel('Counts')
                ax1.set_ylim(5e-1, np.max(y) + 100)
                #ax1.legend(loc='upper left')

                ax2 = ax1.twiny()
                ax2.set_xticks([])

                fig.tight_layout()
                plt.title(f"HV={key}V")
                figname = self.filename[:-5] + '-hist-amplitudes-' + str(key) + 'V.pdf'
                plt.savefig(figname, bbox_inches='tight')
                plt.show()

        self.amplitudes = amplitudes

    def plot_hist_charge(self):

        for key in self.wfDic:
            nr_entries = len(self.wfDic[key])
            nbins = int(nr_entries / 100)

            plt.figure()
            plt.subplot(2, 1, 1)

            charges = []
            for wf in self.wfDic[key]:
                charges.append(wf.charge)

            y, x, _ = plt.hist(charges, bins=nbins)
            plt.yscale('log')
            plt.ylabel('Counts')
            plt.xlabel('Charge [Vs]')
            plt.title(f"Charge Histogram for HV={key}V")
            figname = self.filename[:-5] + '-hist-charge-' + str(key) + 'V.pdf'
            plt.savefig(figname)
            plt.show()

    def plot_hist_gain(self):

        for key in self.wfDic:
            nr_entries = len(self.wfDic[key])
            nbins = int(nr_entries / 100)

            plt.figure()
            plt.subplot(2, 1, 1)

            gains = []
            for wf in self.wfDic[key]:
                gains.append(wf.gain)

            y, x, _ = plt.hist(gains, bins=nbins)
            plt.yscale('log')
            plt.ylabel('Counts')
            plt.xlabel('Gain')
            plt.title(f"Gain Histogram for HV={key}V")
            figname = self.filename[:-5] + '-hist-gain-' + str(key) + 'V.pdf'
            plt.savefig(figname)
            plt.show()

    def plot_hist_charge_gain(self, name, excl=['900', '1300'], frac=1/100):

        def gaussian(x, a, mu, sigma):
            return a * np.exp(- (x - mu) ** 2 / (sigma ** 2))

        gains = {}
        gainSd = {}
        for key in self.wfDic:
            if key not in excl:
                data = []
                for wf in self.wfDic[key]:
                    data.append(wf.charge * 1e12)

                nr_entries = len(data)
                nbins = int(nr_entries*frac)

                entries, edges = np.histogram(data, bins=nbins)
                bin_m = (edges[:-1] + edges[1:]) / 2

                x = bin_m
                y = entries

                Maxima = argrelextrema(y, np.greater, order=5)[0]
                if len(Maxima) >= 2:
                    if x[Maxima[-1]] > -0.1:
                        indMax = Maxima[-2]
                    else:
                        indMax = Maxima[-1]
                else:
                    indMax = Maxima[0]
                yMax = y[indMax]
                Minima = argrelextrema(y, np.less, order=1)[0]

                splitInd = 0
                for i in Minima[Minima > indMax]:
                    prozent = y[i] / yMax
                    if prozent <= 0.25:
                        splitInd = i
                        break
                if splitInd == 0:
                    splitInd = indMax + 5

                mask = np.arange(splitInd + 1)

                a0 = yMax
                mu0 = x[indMax]

                x_halb = x[int(indMax / 2)]
                x_ymax = x[indMax]
                sigma0 = 2 * abs(x_halb + x_ymax)

                xfit = np.linspace(np.min(x), np.max(x), 100)
                popt, pcov = optimize.curve_fit(gaussian, x[mask], y[mask], p0=(a0, mu0, sigma0), maxfev=int(1e4))
                perr = np.sqrt(np.diag(pcov))

                gainMean = abs(popt[1] / 1e12 / const.e)
                gainSd_val = abs(perr[1] / 1e12 / const.e)
                gains[int(key)] = gainMean
                gainSd[int(key)] = gainSd_val

                mask2 = gaussian(xfit, *popt) > 0

                fig, ax1 = plt.subplots()
                ax1.hist(data, bins=nbins, histtype='step', log=True, linewidth=2.0)
                ax1.vlines(x[splitInd], 0, np.max(y) + 100, 'orange', linewidth=2.0, label='fit cutoff')
                ax1.plot(xfit[mask2], gaussian(xfit, *popt)[mask2], color='black', linewidth=2.0,
                         label=r'$\mu$=' + str(np.round(popt[1], 3)) + '\n$\sigma$=' + str(np.round(popt[2], 3)))
                ax1.set_xlabel(r'Charge [$\mu$Vs]')
                ax1.set_ylabel('Counts')
                ax1.set_ylim(5e-1, np.max(y) + 100)
                ax1.legend(loc='upper left')

                ax2 = ax1.twiny()
                ax2.set_xlabel("Gain [1e7]")
                lim1 = np.min(data)
                lim2 = np.max(data)
                ax2.set_xlim(lim1, lim2)
                ticks = np.linspace(lim1, lim2, 8)
                ax2.set_xticks(ticks)
                ticklabels = []
                for t in ticks:
                    tick = np.round(t / 1e12 / const.e / 1e7, 1)  # np.round(t/1e12/const.e,-6)
                    ticklabels.append(tick)
                ax2.set_xticklabels(ticklabels)
                # ax2.ticklabel_format(axis='x', style='sci', scilimits=(0,0))

                fig.tight_layout()
                plt.title('PMT ' +name+ f", HV={key}V") #Charge/Gain Histogram
                figname = self.filename[:-5] + '-hist-charge-gain-' + str(key) + 'V.pdf'
                plt.savefig(figname, bbox_inches='tight')
                plt.show()

        self.gains = gains
        self.gainSd = gainSd

    def plot_gain_hv(self, name):

        gains = self.gains
        gainSd = self.gainSd

        x = list(gains.keys())
        y = list(gains.values())
        dy = list(gainSd.values())

        x = np.array(x, dtype=int)
        dx = []
        for hv in x:
            dhv = hv * (((0.001 / (hv / 250)) ** 2 + (0.05 ** 2)) ** (1 / 2))
            dx.append(dhv)
        y = np.array(y, dtype=float)
        dy = np.array(dy, dtype=float)

        popt, pcov = np.polyfit(x, np.log(y), 1, w=np.sqrt(y), cov=True)
        perr = np.sqrt(np.diag(pcov))
        b = popt[0]
        db = perr[0]
        a = popt[1]
        da = perr[1]

        def fit_fn(x, a, b):
            return np.exp(a) * np.exp(b * x)

        xx = np.linspace(800, 1600, 100000)
        yy = fit_fn(xx, a, b)
        hvs = {}
        for key in [1e6, 5e6, 1e7]:
            hv = xx[np.argmin(np.abs(yy - key))]
            dhv = (1 / b) * ((db ** 2 / b ** 2) * (math.log(key) - a) ** 2 + da ** 2) ** (1 / 2)
            hvs[key] = [hv, dhv]
            # print('HV for gain = ', key / 1e6, '1e6', 'is', hvs[key])
        #hvs_arr = list(hvs.items())
        filename = self.filename[:-5] + '-gain-hv.txt'
        #np.savetxt(filename, hvs_arr, header='gain, HV [V]')
        with open(filename, "w") as file:
            for key, val in hvs.items():
                string = str(key) + "   " + str(val) + "\n"
                file.write(string)

        plt.figure()
        plt.subplot(1, 1, 1)
        plt.errorbar(x, y, xerr=dx, yerr=dy, fmt='none', capsize=5, capthick=2, label="data")
        plt.plot(xx, yy, color='black', linewidth=2.0, label="fit")
        plt.xlim(np.min(x)-100, np.max(x)+100)
        plt.vlines(hvs[5e6][0], 0, 3e7, color='orange', linewidth=2.0, label="HV for 5e6 gain")
        plt.vlines(hvs[1e7][0], 0, 3e7, color='darkorange', linewidth=2.0, label="HV for 1e7 gain")
        plt.semilogy()
        plt.ylim(np.min(y)-1e6, 3e7)
        plt.ylabel('Gain')
        plt.xlabel('HV [V]')
        plt.legend(loc='lower right', fontsize=8)
        plt.title('PMT '+name)
        plt.tight_layout()
        figname = self.filename[:-5] + '-gain-hv.pdf'
        plt.savefig(figname)
        plt.show()

    def plot_ampl_hv(self):

        amplitudes = self.amplitudes
        for key in amplitudes:
            amplitudes[key] = abs(amplitudes[key])

        x = list(amplitudes.keys())
        y = list(amplitudes.values())

        x = np.array(x, dtype=float)
        y = np.array(y, dtype=float)

        p, V = np.polyfit(x, np.log(y), 1, w=np.sqrt(y), cov=True)
        b = p[0]
        a = p[1]

        def fit_fn(x, a, b):
            return np.exp(a) * np.exp(b * x)

        plt.figure()
        plt.subplot(2, 1, 1)
        plt.plot(x, y, 'o', label="data")
        plt.plot(x, fit_fn(x, a, b), color='black', linewidth=2.0, label="fit")
        plt.legend(loc='upper left', fontsize=8)
        plt.yscale('log')
        plt.ylabel('Amplitude [mV]')
        plt.xlabel('HV [V]')
        figname = self.filename[:-5] + '-amplitude-hv.pdf'
        plt.savefig(figname)
        plt.show()

    def get_dark_rate(self, spe, ratio=0.33, width=2):
        if not hasattr(self, 'wfDic'):
            self.loadData
        if not hasattr(spe, 'overallWF'):
            spe.overallSPE

        dark_rate = {}
        for key in self.wfDic:
            threshold = np.min(spe.overallWF[key][1]) * ratio
            if threshold > -2.5:
                threshold = -2.5
            T = self.wfDic[key][0].x[-1] * 1e-9
            n = len(self.wfDic[key])
            count = 0
            totalWidth = 0.0
            for i, wf in enumerate(self.wfDic[key]):
                peaks = find_peaks(-wf.y, height=-threshold, width=width)
                l = len(peaks[0])
                if l > 0:
                    count += l
                    for w in peaks[1]['widths']:
                        totalWidth += w

            time = T * n - totalWidth * 1e-9
            dT = 0.2 * 1e-9
            dtime = time * (dT / T)
            dcount = count**(1/2)
            rate = count / time
            drate = rate * (dcount/count) #rate * ((dtime / time) ** 2 + (dcount / count) ** 2) ** (1 / 2)
            print('HV [V]:', key, ', Nr. of WFs:', n, ', Threshold [mV]:', threshold)
            print('Counts:', count, ', Time [s]:', time, ', Rate [Hz]:', rate, '+-', drate)
            print('-----------------------------')
            dark_rate[key] = [rate, drate]

        filename = self.filename[:-5] + '-dark-rate-ratio' + str(ratio) + '-width' + str(width) + 'ns.txt'
        #fmt = '%d', '%1.9f'
        #np.savetxt(filename, dark_rate_arr, header='HV [V], dark rate [Hz]', fmt=fmt)

        with open(filename, "w") as file:
            for key, val in dark_rate.items():
                string = str(key) + "   " + str(val) + "\n"
                file.write(string)

    def plot_peaks(self, spe, ratio=0.33, width=2):

        for key in self.wfDic:
            plt.figure()
            threshold = np.min(spe.overallWF[key][1]) * ratio
            for i, wf in enumerate(self.wfDic[key]):
                peaks = find_peaks(-wf.y, height=-threshold, width=width)
                l = len(peaks[0])
                if l > 0:
                    plt.plot(wf.x, wf.y, 'green')
                if l == 0:
                    plt.plot(wf.x, wf.y, 'yellow')

            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.title(f"Dark Waveforms for HV={key}V")
            plt.axhline(y=threshold, color='red', linestyle='--')
            plt.show()

    def plot_peaks_old(self, peaks_dic, threshold=-2, width=3):

        peaks_dic2 = {}
        for i in sorted(peaks_dic):
            peaks_dic2[i] = peaks_dic[i]

        cmap = plt.cm.viridis
        for key in peaks_dic2:
            plt.figure()
            colors = iter(cmap(np.linspace(0, 0.7, 10)))
            for i in range(10):
                for j, c in zip(peaks_dic2[key][i], colors):
                    plt.plot(peaks_dic2[key][i][j][-1].x, peaks_dic2[key][i][j][-1].y, color=c)
                    for k in peaks_dic2[key][i][j][0][0]:
                        plt.plot(peaks_dic2[key][i][j][-1].x[k], peaks_dic2[key][i][j][-1].y[k], 'yo')
            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.title(f"Waveforms for HV={key}V")
            plt.axhline(y=threshold, color='olive', linestyle='--')

            figname = self.filename[:-5] + '-waveforms-peaks-at' + str(key) + 'V-threshold' + str(threshold) + 'mV-width' +\
                      str(width) + '.pdf'
            plt.savefig(figname)
            plt.show()

    def tt(self, trigger, ratio=0.33):

        if not hasattr(self, 'wfDic'):
            self.loadData
        if not hasattr(self, 'overallWF'):
            self.overallSPE

        TT_all = {}
        for key1, key2 in zip(self.wfDic, trigger.wfDic):
            TT = []
            threshold = np.min(self.overallWF[key1][1]) * ratio
            for wf, tr in zip(self.wfDic[key1], trigger.wfDic[key2]):
                xs = wf.x[wf.mask]
                ys = wf.y[wf.mask]
                xt = tr.x
                yt = tr.y

                mask1 = ys <= threshold
                if len(xs[mask1]) > 0:
                    t_spe = xs[mask1][0]

                    Spline = US(xt, yt)
                    xt_new = np.linspace(xt[0], xt[-1], 10000)
                    yt_new = Spline(xt_new)
                    mask2 = yt_new >= 1500
                    t_tr = xt_new[mask2][0]

                    tt_val = t_spe - t_tr
                    TT.append(tt_val)

            TT_all[key1] = TT

        self.TT = TT_all

    def plot_tt(self, name, binsize=0.4):

        TT_all = self.TT
        dTT = 0.4
        TTS = {}

        def gaussian(x, a, mu, sigma):
            return a * np.exp(- (x - mu) ** 2 / (sigma ** 2))

        for key in TT_all:
            data = TT_all[key]

            bins = np.arange(np.min(data), np.max(data), binsize)
            entries, edges = np.histogram(data, bins=bins)
            bin_m = (edges[:-1] + edges[1:])/2

            x = bin_m
            y = entries

            yMax = np.max(y)
            indMax = np.argmax(y)
            a0 = yMax
            mu0 = x[indMax]

            x_halb = x[int(indMax/2)]
            x_ymax = x[indMax]
            sigma0 = 2 * abs(x_halb + x_ymax)

            popt, pcov = optimize.curve_fit(gaussian, x, y, p0=(a0, mu0, sigma0), maxfev=int(1e4))
            perr = np.sqrt(np.diag(pcov))
            a = popt[0]
            da = perr[0]
            mu = popt[1]
            dmu = perr[1]
            sigma = popt[2]
            dsigma = perr[2]
            y_val = a / 2
            dy_val = da / 2

            fehler1 = (da ** 2) * ((sigma ** 2) / (4 * a ** 2)) * ((-math.log(1/2)) ** (-1))
            fehler2 = dmu ** 2
            fehler3 = (dsigma ** 2) * (-math.log(1/2))
            fehler4 = (dy_val ** 2) * ((sigma ** 2) / (4 * y_val ** 2)) * ((-math.log(1/2)) ** (-1))

            dx = (fehler1 + fehler2 + fehler3 + fehler4) ** (1 / 2)

            xfit = np.linspace(np.min(x), np.max(x), 10000)
            yfit = gaussian(xfit, *popt)
            mask2 = yfit >= a / 2
            x1 = xfit[mask2][0]
            x2 = xfit[mask2][-1]

            tts_val = x2 - x1
            dtts = (2*(dx**2))**(1/2)
            TTS[key] = [tts_val, dtts]
            print(tts_val, dtts)

            plt.figure()
            plt.hist(x=edges[:-1], bins=edges, weights=entries, histtype='step', linewidth=2.0)
            plt.plot(xfit, gaussian(xfit, *popt), color='black', linewidth=2.0,
                     label=r'$\mu$=' + str(np.round(popt[1], 3)) + '\n$\sigma$=' + str(np.round(popt[2], 3)))
            plt.hlines(y_val, x1, x2, 'orange', linewidth=3.0,
                       label='FWHM=' + str(np.round(tts_val, 2))+r'$\pm$'+str(np.round(dtts,2)))
            plt.xlabel('Transit time [ns]')
            plt.ylabel('Counts')
            plt.xlim(x[indMax-12], x[indMax+12])
            plt.legend()
            plt.title(name + f', HV={key} V')
            figname = self.filename[:-5] + '-TTS-' + str(key) +'V.pdf'
            plt.savefig(figname)
            plt.show()

        self.TTS = TTS
        filename = self.filename[:-5] + '-TTS.txt'
        with open(filename, "w") as file:
            for key, val in TTS.items():
                string = str(key) + "   " + str(val) + "\n"
                file.write(string)