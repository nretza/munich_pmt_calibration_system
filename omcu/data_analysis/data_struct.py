#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np
import math
import os

from scipy import optimize
from scipy.signal import find_peaks
from scipy.signal import argrelextrema
from scipy.interpolate import UnivariateSpline as US
import scipy.constants as const

from utils.util import *
from utils.Waveform import Waveform
import config

#TODO: logging, printouts, other analysis

class data_struct:

    def __init__(self, signal_data, trigger_data, metadict=None, filename = "", filepath = ""):

        if metadict == None:
            metadict = {
                "theta":            -1,
                "phi":              -1,
                "HV":               -1,
                "Powermeter":       -1,
                "Laser temp":       -1,
                "Laser tune":       -1,
                "Laser freq":       -1,
                "sgnl_threshold":   -1,
                "occ":              -1,
                "gain":             -1,
                }

        self.metadict = metadict
        self.signalset  = signal_data
        self.triggerset = trigger_data
        self.filename = filename
        self.filepath = filepath

        self.wf_list = []

        for wf_data in self.signalset:
                wf = Waveform(self.metadict["theta"],
                              self.metadict["phi"],
                              self.metadict["HV"],
                              wf_data[:, 0],
                              wf_data[:, 1],
                              np.min(wf_data[:, 1]))
                wf.mean()
                wf.calculate_gain()
                self.wf_list.append(wf)

        self.trg_list = []

        for trg_data in self.triggerset:
                wf = Waveform(self.metadict["theta"],
                              self.metadict["phi"],
                              self.metadict["HV"],
                              trg_data[:, 0],
                              trg_data[:, 1],
                              np.min(trg_data[:, 1]))
                self.trg_list.append(wf)

    def get_average_wf(self):
        xValues = np.array([wf.x for wf in self.wf_list])
        averageX = np.mean(xValues, axis=0)
        yValues = np.array([wf.y for wf in self.wf_list])
        averageY = np.mean(yValues, axis=0)
        indMin = np.argmin(averageY)
        xlim1 = averageX[indMin-10]
        xlim2 = averageX[indMin+15]
        self.mask = (averageX >= xlim1) & (averageX <= xlim2)
        self.average_wf = (averageX, averageY)


    def validate_gain(self, delta=10):
        assert (self.metadict["gain"] - calculate_gain(self.dataset, self.metadict["sgnl_threshold"])) < delta

    def get_baseline_mean(self):
        means = [wf.mean for wf in self.wf_list]
        self.HVmean = (np.mean(means), np.std(means))
        return self.HVmean

    def subtractBaseline(self, baseline=None):
        if baseline == None:
            baseline = self.get_baseline_mean()
        for wf in self.wf_list:
            wf.subtractBaseline(baseline[0])

    def get_dark_count_rate(self):
        pass

    def plot_wfs(self, number=10, threshold=-3):

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, number)))
        plt.figure()

        for wf, c in zip(self.wf_list, colors):
            if wf.min < threshold:
                plt.plot(wf.x, wf.y, color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.title(f"Waveforms for HV={self.metadict['HV']}V, phi={self.metadict['phi']}, theta={self.metadict['theta']}, threshold={threshold}")
        figname = f"{self.filename[:-5]}-waveforms-HV={self.metadict['HV']}V_phi={self.metadict['phi']}_theta={self.metadict['theta']}_threshold={threshold}.pdf"
        save_dir = os.path.join(self.filepath, "wf")
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def plot_peaks(self, ratio=0.33, width=2):

        if not hasattr(self, 'average_wf'):
            self.get_average_wf()

        plt.figure()
        threshold = np.min(self.average_wf[1]) * ratio
        for wf in self.wf_list:
            peaks = find_peaks(-wf.y, height=-threshold, width=width)
            l = len(peaks[0])
            if l > 0:
                plt.plot(wf.x, wf.y, 'green')
            if l == 0:
                plt.plot(wf.x, wf.y, 'yellow')

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.axhline(y=threshold, color='red', linestyle='--')
        plt.title(f"Waveform peaks for HV={self.metadict['HV']}V, phi={self.metadict['phi']}, theta={self.metadict['theta']}, threshold={threshold}")
        figname = f"{self.filename[:-5]}-waveform_peaks_HV={self.metadict['HV']}V_phi={self.metadict['phi']}_theta={self.metadict['theta']}_threshold={threshold}.pdf"
        save_dir = os.path.join(self.filepath, "wf")
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def plot_wfs_mask(self, number=10, threshold=-3):

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, number)))
        plt.figure()

        for wf, c in zip(self.wf_list, colors):
            if wf.min < threshold:
                plt.plot(wf.x[wf.mask], wf.y[wf.mask], color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.title(f"Waveforms Mask for HV={self.metadict['HV']}V, phi={self.metadict['phi']}, theta={self.metadict['theta']}, threshold={threshold}")
        figname = f"{self.filename[:-5]}-waveforms_mask_HV={self.metadict['HV']}V_phi={self.metadict['phi']}_theta={self.metadict['theta']}_threshold={threshold}.pdf"
        save_dir = os.path.join(self.filepath, "wf")
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def plot_average_wf(self):
        if not hasattr(self, 'average_wf'):
            self.get_average_wf()
        plt.figure()
        plt.plot(self.average_wf[0], self.average_wf[1])
        plt.xlabel('Time [ns]')
        plt.ylabel('Voltage [mV]')
        plt.title(f"Average waveform for HV={self.metadict['HV']}V, phi={self.metadict['phi']}, theta={self.metadict['theta']}")
        figname = f"{self.filename[:-5]}-average_waveforms_HV={self.metadict['HV']}V_phi={self.metadict['phi']}_theta={self.metadict['theta']}.pdf"
        save_dir = os.path.join(self.filepath, "wf")
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def plot_hist(self, mode="amplitude",exclude=['900', '1300']):

        if self.metadict["HV"] in exclude:
            return

        if mode not in ["amplitude", "gain", "charge"]:
            return

        if mode == "amplitude":
            data = [wf.min for wf in self.wf_list]
        if mode == "gain":
            data = [wf.gain for wf in self.wf_list]
        if mode == "charge":
            data = [wf.charge for wf in self.wf_list]

        nr_entries = len(self.wf_list)
        nbins = int(nr_entries / 100)
        entries, edges = np.histogram(data, bins=nbins)
        bin_m = (edges[:-1] + edges[1:]) / 2

        x = bin_m
        y = entries

        fig, ax1 = plt.subplots()
        ax1.hist(data, bins=nbins, histtype='step', log=True, linewidth=2.0)

        if mode == "amplitude":
            ax1.set_xlabel('Amplitude [mV]')
        if mode == "gain":
            ax1.set_xlabel('Gain')
        if mode == "charge":
            ax1.set_xlabel('Charge')
        ax1.set_ylabel('Counts')
        ax1.set_ylim(5e-1, np.max(y) + 100)
        #ax1.legend(loc='upper left')

        ax2 = ax1.twiny()
        ax2.set_xticks([])

        fig.tight_layout()
        plt.title(f"Waveform {mode}s for HV={self.metadict['HV']}V, phi={self.metadict['phi']}, theta={self.metadict['theta']}")
        figname = f"{self.filename[:-5]}-hist-{mode}s-HV={self.metadict['HV']}V_phi={self.metadict['phi']}_theta={self.metadict['theta']}.pdf"

        save_dir = os.path.join(self.filepath, "hist")
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        plt.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def get_transit_times(self, ratio=0.33):

        if not hasattr(self, "average_wf"):
            self.get_average_wf()

        TT = []
        threshold = np.min(self.average_wf[1]) * ratio
        for wf, tr in zip(self.wf_list, self.trg_list):
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

        self.transit_times = TT
        return self.transit_times

    def plot_transit_times(self, binsize=0.4):

        if not hasattr(self, "transit_times"):
            self.get_transit_times()

        bins = np.arange(np.min(self.transit_times), np.max(self.transit_times), binsize)
        entries, edges = np.histogram(self.transit_times, bins=bins)
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
        plt.title(f"TTS for HV={self.metadict['HV']}V, phi={self.metadict['phi']}, theta={self.metadict['theta']}")
        figname = f"{self.filename[:-5]}-TTS-HV={self.metadict['HV']}V_phi={self.metadict['phi']}_theta={self.metadict['theta']}.pdf"
        save_dir = os.path.join(self.filepath, "transit_time")
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')
