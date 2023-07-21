#!/usr/bin/python3

import logging
import os
from datetime import datetime

import config
import h5py
import numpy as np
from devices.Laser import Laser
from devices.Powermeter import Powermeter
from devices.Rotation import Rotation
from devices.uBase import uBase
from matplotlib import pyplot as plt
from scipy import optimize
from scipy.signal import find_peaks
from scipy.stats import norm
from utils.Waveform import Waveform


#placed here to avoid circular imports
def gaussian(x, a, mu, sigma):
    return a * np.exp(- (x - mu) ** 2 / (2 * sigma ** 2))


class Measurement:

    # class designed to handle a measurement (multiple waveforms taken in bulk)

    def __init__(self,
                 waveform_list=None,
                 signal_data=np.array([]),
                 trigger_data=np.array([]),
                 time_data=np.array([]),
                 metadict=None,
                 filename=None,
                 filepath=None,
                 hdf5_key=None,
                 pmt_id  =None):

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")

        self.filtered_by_threshold = False

        self.default_metadict = {
                "pmt_id":                      -1,
                "time":                        -1,
                "theta [°]":                   -1,
                "phi [°]":                     -1,
                "HV [V]":                      -1,
                "Dy10 [V]":                    -1,
                "Powermeter [pW]":             -1,
                "Picoamp [nA]":                -1,
                "Laser satus":                 -1,
                "Laser temp [°C]":             -1,
                "Laser tune [%]":              -1,
                "Laser pulse freq [Hz]":       -1,
                "Laser wavelength [nm]":       -1,
                "darkbox temp [°C]":           -1,
                "sgnl threshold [mV]":         -1,
                "occ [%]":                     -1,
                "avg amplitude [mV]":          -1,
                "std amplitude [mV]":          -1,
                "gain":                        -1,
                "gain spread":                 -1,
                "charge [pC]":                 -1,
                "charge spread [pC]":          -1,
                "baseline [mV]":               -1,
                "baseline spread [mV]":        -1,
                "peak to valley ratio":        -1,
                "peak to valley ratio spread": -1,
                "rise time [ns]":              -1,
                "rise time spread [ns]":       -1,
                "transit time [ns]":           -1,
                "transit time spread [ns]":    -1,
                "dark count [Hz]":             -1,
                "ringing":                     -1,
                "pre pulse":                   -1,
                "post pulse":                  -1
                }

        self.waveforms = [] # needed for logger warnings to work correctly
        self.metadict  = self.default_metadict

        if waveform_list or signal_data.size or trigger_data.size or time_data.size:
            self.setWaveforms(waveforms=waveform_list, signal=signal_data, trigger=trigger_data, time=time_data)

        if metadict:
            self.setMetadict(metadict)

        self.setFilename(filename)
        self.setFilepath(filepath)
        self.setHDF5_key(hdf5_key)
        self.setPMT_ID(pmt_id)

###-----------------------------------------------------------------

    def setWaveforms(self, waveforms = None, signal = np.array([]), trigger = np.array([]), time = np.array([])):
        if waveforms:
            if signal.size or trigger.size or time.size:
                self.logger.warning("Both Waveforms and signal arrays handed to data struct. Will only use waveforms!")
            self.waveforms = waveforms
        elif signal.size and trigger.size and time.size:
            self.waveforms = []
            for time_i, signal_i, trigger_i in zip(time, signal, trigger):
                self.waveforms.append(Waveform(time=time_i, signal=signal_i, trigger=trigger_i))
        else: raise Exception("ERROR: either waveforms or signal, trigger and time arrays need to be handed over")

    def getWaveforms(self):
        return self.waveforms

    def setMetadict(self, metadict):
        if not metadict: return # check for None
        self.metadict = metadict
        for key in self.default_metadict:
            if key not in self.metadict.keys():
                self.metadict[key] = self.default_metadict[key]

    def getMetadict(self):
        return self.metadict

    def setFilename(self, filename):
        self.filename = filename

    def getFilename(self):
        return self.filename

    def setFilepath(self, filepath):
        self.filepath = filepath

    def getFilepath(self):
        return self.filepath

    def setHDF5_key(self, key):
        self.hdf5_key = key

    def getHDF5_Key(self):
        return self.hdf5_key

    def setPMT_ID(self, pmt_id):
        self.pmt_id = pmt_id

    def getPMT_ID(self):
        if self.pmt_id:     return self.pmt_id
        elif self.filepath: return os.path.basename(self.filepath)
        else:               return None

###-----------------------------------------------------------------

    def __len__(self):
        return len(self.waveforms)

###-----------------------------------------------------------------

    def calculate_occ(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating occupancy without having Waveforms stored!")
        if self.filtered_by_threshold:
            print("WARNING: calculating occupancy on filtered Dataset. Value might be incorrect")
            self.logger.warning("calculating occupancy on filtered Dataset. Value might be incorrect")
        i = 0
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: i +=1
        if float(len(self.waveforms)) == 0: return 0,0
        return float(i)/float(len(self.waveforms))
    
    
    def calculate_avg_amplitude(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating occupancy without having Waveforms stored!")
        amplitudes = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold:
                amplitudes = np.append(amplitudes, wf.min_value)
        if len(amplitudes) == 0: return 0,0
        finite_amplitudes = np.extract(np.isfinite(amplitudes), amplitudes)
        mean, FWHM = norm.fit(finite_amplitudes)
        return mean, FWHM
        # return np.mean(amplitudes), np.std(amplitudes)


    def calculate_gain(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating gain without having Waveforms stored!")
        gains = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold:
                gains = np.append(gains, wf.calculate_gain())
        if len(gains) == 0: return 0,0
        mean, FWHM = norm.fit(gains)
        return mean, FWHM
        # return np.mean(gains), np.std(gains)

    def validate_gain(self, delta=10):
        return (self.metadict["gain"] - self.calculate_gain(self.metadict["sgnl_threshold"])[0]) < delta


    def calculate_charge(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating charge without having Waveforms stored!")
        charges = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: charges = np.append(charges, wf.calculate_charge())
        if len(charges) == 0: return 0,0
        finite_charges = np.extract(np.isfinite(charges), charges)
        mean, FWHM = norm.fit(finite_charges)
        return mean, FWHM
        # return np.mean(charges), np.std(charges)
    

    def calculate_ptv(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating peak to valley ratio without having Waveforms stored!")
        ptv = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold:
                ptv = np.append(ptv, wf.peak_to_valley_ratio)
        if len(ptv) == 0: return 0,0
        finite_ptv = np.extract(np.isfinite(ptv), ptv)
        mean, FWHM = norm.fit(finite_ptv)
        return mean, FWHM
        # return np.mean(ptv), np.std(ptv)


    def calculate_baseline(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating baseline without having Waveforms stored!")
        baseline = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold:
                baseline = np.append(baseline, wf.baseline)
        if len(baseline) == 0: return 0,0
        finite_baseline = np.extract(np.isfinite(baseline), baseline)
        mean, FWHM = norm.fit(finite_baseline)
        return mean, FWHM
        # return np.mean(baseline), np.std(baseline)


    def calculate_rise_time(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating rise time without having Waveforms stored!")
        rise_times = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: rise_times = np.append(rise_times, wf.rise_time)
        if len(rise_times) == 0: return 0,0
        finite_rise_times = np.extract(np.isfinite(rise_times), rise_times)
        mean, FWHM = norm.fit(finite_rise_times)
        return mean, FWHM
        # return np.mean(rise_times), np.std(rise_times)


    def calculate_transit_time(self, signal_threshold, nr_bins = 5000):

        if not self.waveforms: self.logger.warning("calculating transit time without having Waveforms stored!")
        transit_times = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: transit_times = np.append(transit_times, wf.transit_time)
        if len(transit_times) == 0: return 0,0

        hist, bins = np.histogram(transit_times, bins=nr_bins)

        mask = np.ones(nr_bins, dtype=bool) & (hist[:] != 0)
        x_fit = bins[:-1][mask] + np.diff(bins)[0] / 2
        y_fit = hist[mask]

        popt, _ = optimize.curve_fit(gaussian, x_fit, y_fit, p0=[np.max(y_fit), np.mean(x_fit), np.std(x_fit)])
        FWHM = abs(2 * np.sqrt(2 * np.log(2)) * popt[2])

        return popt[1], FWHM


    def get_average_wf(self):
        if not self.waveforms: self.logger.warning("calculating average WF without having Waveforms stored!")
        xValues = np.array([wf.time for wf in self.waveforms])
        averageX = np.mean(xValues, axis=0)
        yValues = np.array([wf.signal for wf in self.waveforms])
        averageY = np.mean(yValues, axis=0)
        return (averageX, averageY)


    def get_baseline_mean(self):
        if not self.waveforms: self.logger.warning("calculating baseline without having Waveforms stored!")
        means = [wf.mean for wf in self.waveforms]
        mean, FWHM = norm.fit(means)
        return mean, FWHM
        # return np.mean(means), np.std(means)


    def subtract_baseline(self, baseline=None):
        if not self.waveforms: self.logger.warning("subtracting baseline without having Waveforms stored!")
        if baseline == None:
            baseline = self.get_baseline_mean()
        for wf in self.waveforms:
            wf.subtract_baseline(baseline[0])


    def filter_by_threshold(self, signal_threshold):
        if not self.waveforms: self.logger.warning("filter Waveforms without having Waveforms stored!")
        self.waveforms = [wf for wf in self.waveforms if wf.min_value <= signal_threshold]
        self.filtered_by_threshold = True


    def filter_by_gain(self, gain_threshold):
        if not self.waveforms: self.logger.warning("filter Waveforms without having Waveforms stored!")
        self.waveforms = [wf for wf in self.waveforms if wf.calculate_gain() >= gain_threshold]
        self.filtered_by_threshold = True


    def measure_metadict(self, signal_threshold, only_waveform_characteristics=False):

        meta_dict = self.metadict
        
        if not only_waveform_characteristics:	
            meta_dict["pmt_id"]                = self.getPMT_ID() if self.getPMT_ID() else -1
            meta_dict["time"]                  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            meta_dict["theta [°]"]             = round( Rotation.Instance().get_position()[1],    2)
            meta_dict["phi [°]"]               = round( Rotation.Instance().get_position()[0],    2)
            meta_dict["Dy10 [V]"]              = round( uBase.Instance().getDy10(),               2)
            meta_dict["Powermeter [pW]"]       = round( Powermeter.Instance().get_power() * 1e12, 3)
            meta_dict["Laser satus"]           = Laser.Instance().get_ld()
            meta_dict["Laser temp [°C]"]       = round( Laser.Instance().get_temp(),              2)
            meta_dict["Laser tune [%]"]        = round( Laser.Instance().get_tune_value()/10,     2)
            meta_dict["Laser pulse freq [Hz]"] = round( Laser.Instance().get_freq(),              2)
            meta_dict["sgnl threshold [mV]"]   = round( signal_threshold,                         2)
                
        meta_dict["occ [%]"]                     = round(self.calculate_occ(signal_threshold) * 100,          3)
        meta_dict["avg amplitude [mV]"]          = round(self.calculate_avg_amplitude(signal_threshold)[0],   3)
        meta_dict["std amplitude [mV]"]          = round(self.calculate_avg_amplitude(signal_threshold)[1],   3)
        meta_dict["gain"]                        = round(self.calculate_gain(signal_threshold)[0],            3)
        meta_dict["gain spread"]                 = round(self.calculate_gain(signal_threshold)[1],            3)
        meta_dict["charge [pC]"]                 = round(self.calculate_charge(signal_threshold)[0] * 1e12,   3)
        meta_dict["charge spread [pC]"]          = round(self.calculate_charge(signal_threshold)[1] * 1e12,   3)
        meta_dict["rise time [ns]"]              = round(self.calculate_rise_time(signal_threshold)[0],       3)
        meta_dict["rise time spread [ns]"]       = round(self.calculate_rise_time(signal_threshold)[1],       3)
        meta_dict["transit time [ns]"]           = round(self.calculate_transit_time(signal_threshold)[0],    3)
        meta_dict["transit time spread [ns]"]    = round(self.calculate_transit_time(signal_threshold)[1],    3)
        meta_dict["baseline [mV]"]               = round(self.calculate_baseline(signal_threshold)[0],        3)
        meta_dict["baseline spread [mV]"]        = round(self.calculate_baseline(signal_threshold)[1],        3)
        meta_dict["peak to valley ratio"]        = round(self.calculate_ptv(signal_threshold)[0],             3)
        meta_dict["peak to valley ratio spread"] = round(self.calculate_ptv(signal_threshold)[1],             3)

        self.setMetadict(meta_dict)

        return meta_dict

###-----------------------------------------------------------------

    def write_to_file(self, hdf5_connection=None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'a')
            close_on_end = True

        h5_key = self.hdf5_key if self.hdf5_key else f"HV{self.metadict['Dy10 [V]']}/theta{self.metadict['theta [°]']}/phi{self.metadict['phi [°]']}"
        dataset = hdf5_connection.create_dataset(f"{h5_key}/dataset",
                                                 (len(self.waveforms), len(self.waveforms[0].time), 3),
                                                 dtype=np.float32,
                                                 compression="gzip",
                                                 compression_opts=6)

        dataset[:,:,0] = [wf.time for wf in self.waveforms]
        dataset[:,:,1] = [wf.signal for wf in self.waveforms]
        dataset[:,:,2] = [wf.trigger for wf in self.waveforms]

        for key in self.metadict:
            dataset.attrs[key] = self.metadict[key]

        if close_on_end:
            hdf5_connection.close()


    def read_from_file(self, hdf5_connection=None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'r')
            close_on_end = True

        dataset = hdf5_connection[self.hdf5_key]["dataset"]

        metadict = {}
        for key in dataset.attrs.keys():
            metadict[key] = dataset.attrs[key]
        self.setMetadict(metadict)

        self.setWaveforms(time=dataset[:,:,0], signal=dataset[:,:,1], trigger=dataset[:,:,2])

        if close_on_end:
            hdf5_connection.close()
    

    def read_metadict_from_file(self, hdf5_connection = None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'r')
            close_on_end = True

        dataset = hdf5_connection[self.hdf5_key]["dataset"]

        metadict = {}
        for key in dataset.attrs.keys():
            metadict[key] = dataset.attrs[key]
        self.setMetadict(metadict)

        if close_on_end:
            hdf5_connection.close()


    def clear(self):

        # clears the waveform list (in an attempt to use less memory when not needed)

        del self.waveforms
        self.waveforms = []

###-----------------------------------------------------------------

    # TODO Plotting

    def plot_wfs(self, how_many):

        if not self.waveforms:
            print("plotting waveforms without having Waveforms stored!")
            return

        fig, ax = plt.subplots()

        cmap    = plt.cm.viridis
        colors  = cmap(np.linspace(0, 0.7, how_many))

        for wf, c in zip(self.waveforms[:how_many], colors):
            ax.plot(wf.time, wf.signal, color=c)

        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Voltage (mV)')

        ax.axvline(x=self.waveforms[0].trigger_time, color='grey', ls=":", label="trigger time")
        ax.axhline(y=self.metadict["sgnl threshold [mV]"], color='tab:orange', ls="--", label=f"signal threshold ({self.metadict['sgnl threshold [mV]']} mV)")
        ax.legend()

        ax.set_title(f"Waveforms for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        
        figname = f"{self.filename[:-5]}-waveforms_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5], "waveforms")
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_peaks(self, ratio=0.33, width=2, how_many=10):

        if not self.waveforms:
            print("plotting waveform peaks without having Waveforms stored!")
            return

        average_wf = self.get_average_wf()
        threshold = np.min(average_wf[1]) * ratio

        fig, ax = plt.subplots()
        for i in range(how_many):
            wf = self.waveforms[i]
            peaks = find_peaks(-wf.signal, height=-threshold, width=width)
            l = len(peaks[0])
            color = "yellow" if l == 0 else "green"
            ax.plot(wf.time, wf.signal, color=color)

        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Voltage (mV)')

        ax.axvline(x=self.waveforms[0].trigger_time, color='grey', ls=":", label="trigger time")
        ax.axhline(y=threshold, color='red', linestyle='--', label="threshold")
        ax.legend()

        title = f"Waveform Peaks for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}"
        ax.set_title(title)

        figname = f"{self.filename[:-5]}-waveform_peaks_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5],  "waveform-peaks")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), dpi = 300)
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()



    def plot_wf_masks(self, how_many=10):

        if not self.waveforms:
            print("plotting waveform masks without having Waveforms stored!")
            return

        cmap = plt.cm.viridis
        colors = cmap(np.linspace(0, 0.7, how_many))

        fig, ax = plt.subplots()

        for wf, c in zip(self.waveforms[:how_many], colors):
            ax.plot(wf.time[wf.mask], wf.signal[wf.mask], color=c)

        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Voltage (mV)')

        ax.axvline(x=self.waveforms[0].trigger_time, color='grey', ls=":", label="trigger time")
        ax.axhline(y=self.metadict["sgnl threshold [mV]"], color='tab:orange', ls="--", label=f"signal threshold ({self.metadict['sgnl threshold [mV]']} mV)")
        ax.legend()
        
        ax.set_title(f"Waveform Masks for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        
        figname = f"{self.filename[:-5]}-waveform_masks_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5], "waveform-masks")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), dpi = 300)
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()



    def plot_average_wf(self):

        if not self.waveforms:
            print("plotting average waveform without having Waveforms stored!")
            return
        
        average_wf = self.get_average_wf()

        fig, ax = plt.subplots()

        ax.plot(average_wf[0], average_wf[1])

        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Voltage (mV)')

        ax.axvline(x=self.waveforms[0].trigger_time, color='grey', ls=":", label="trigger time")
        ax.axhline(y=self.metadict["sgnl threshold [mV]"], color='tab:orange', ls="--", label=f"signal threshold ({self.metadict['sgnl threshold [mV]']} mV)")
        ax.legend()
        
        ax.set_title(f"Average Waveform for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        
        figname = f"{self.filename[:-5]}-average_waveform_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5], "average-waveform")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), dpi = 300)
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_ampl_to_gain(self):

        ampl_list = []
        gain_list = []
        for wf in self.waveforms:
            ampl_list.append(wf.min_value)
            gain_list.append(wf.calculate_gain())

        fig, ax = plt.subplots()

        ax.scatter(np.array(ampl_list), np.array(gain_list))

        ax.set_xlabel("amplitude [mV]")
        ax.set_ylabel("gain")

        ax.set_title(f"amplitude to gain correlation")

        figname = f"{self.filename[:-5]}-ampl_to_gain.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5], "correlations")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), dpi = 300)
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_hist(self, mode="amplitude", nr_bins=None, fitting_threshold=None, log_scale=False):

        # TODO: twin axis for two histograms

        if not self.waveforms:
            print(f"plotting {mode}-histogram without having Waveforms stored!")
            return

        if mode not in ["amplitude", "gain", "charge", "amplitude_all"]:
            return

        if mode == "amplitude": data = [wf.min_value for wf in self.waveforms]
        if mode == "gain":      data = [wf.calculate_gain() for wf in self.waveforms]
        if mode == "charge":    data = [wf.calculate_charge() for wf in self.waveforms]
        if mode == "amplitude_all": data = [value for wf in self.waveforms for value in wf.signal]

        if not nr_bins:
            nr_bins = min(max(int(len(data) / 100), 10), 500)

        fig, ax = plt.subplots()

        counts, bins, _ = ax.hist(data, bins=nr_bins, histtype='step', log=False, linewidth=2.0)

        if mode == "amplitude": ax.set_xlabel('Amplitude [mV]')
        if mode == "gain":      ax.set_xlabel('Gain')
        if mode == "charge":    ax.set_xlabel('Charge [pC]')
        if mode == "amplitude_all": ax.set_xlabel('Amplitude [mV]')
        ax.set_ylabel('Counts')

        if mode == "amplitude": plt.axvline(x=self.metadict["sgnl threshold [mV]"], color='black', ls=":", label="trigger threshold")
        if mode == "amplitude_all": plt.axvline(x=self.metadict["sgnl threshold [mV]"], color='black', ls=":", label="trigger threshold")

        # fitting

        if mode == "amplitude":     mask = (bins[:-1] <= fitting_threshold) if fitting_threshold else np.ones(nr_bins, dtype=bool)
        if mode == "amplitude_all": mask = (bins[:-1] <= fitting_threshold) if fitting_threshold else np.ones(nr_bins, dtype=bool)
        if mode == "charge":        mask = (bins[:-1] <= fitting_threshold) if fitting_threshold else np.ones(nr_bins, dtype=bool)
        if mode == "gain":          mask = (bins[:-1] >= fitting_threshold) if fitting_threshold else np.ones(nr_bins, dtype=bool)

        mask = mask & (counts[:] != 0)

        x_fit = bins[:-1][mask] + np.diff(bins)[0]/2
        x_all = np.linspace(np.min(bins), np.max(bins), 10000)
        y_fit = counts[mask]

        try:
            popt, _ = optimize.curve_fit(gaussian, x_fit, y_fit, p0=[np.max(y_fit), np.mean(x_fit), np.std(x_fit)])
            fwhm = 2 * np.sqrt(2 * np.log(2)) * popt[2]

            ax.plot(x_all, gaussian(x_all, *popt), 'r-', label='Gaussian fit')
            ax.plot((popt[1] - (fwhm / 2), popt[1] + (fwhm / 2)), (popt[0]/2, popt[0]/2), color='black', label=f"FWHM ({fwhm:.2f} mV)")
            ax.axvline(x=popt[1] - (fwhm / 2), color="tab:orange", ls="--")
            ax.axvline(x=popt[1] + (fwhm / 2), color="tab:orange", ls="--")

        except RuntimeError:
            print(f"could not fit {mode} histogram on key {self.hdf5_key}")
            self.logger.warning(f"could not fit {mode} histogram on key {self.hdf5_key}")

        if log_scale:
            ax.set_yscale('log')
            ax.set_ylim(bottom = 1e-1)

        ax.legend()

        ax.set_title(f"Waveform {mode}s for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        
        figname = f"{self.filename[:-5]}-hist_{mode}s_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5],  f"{mode}-histograms")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_transit_times(self, nr_bins=None, x_min = 110, x_max = 155):

        if not self.waveforms:
            print(f"plotting transit times without having Waveforms stored!")
            return

        transit_times = [wf.transit_time for wf in self.waveforms]

        if not nr_bins:
            nr_bins = max(int(len(transit_times) / 100), 10)

        fig, ax = plt.subplots()

        hist, bins, _ = ax.hist(transit_times, histtype='step', bins=nr_bins, linewidth=2.0)

        mask = np.ones(nr_bins, dtype=bool) & (hist[:] != 0)
        x_fit = bins[:-1][mask] + np.diff(bins)[0] / 2
        x_all = np.linspace(np.min(bins), np.max(bins), 10000)
        y_fit = hist[mask]

        popt, _ = optimize.curve_fit(gaussian, x_fit, y_fit, p0=[np.max(y_fit), np.mean(x_fit), np.std(x_fit)])
        fwhm = abs(2 * np.sqrt(2 * np.log(2)) * popt[2])

        ax.plot(x_all, gaussian(x_all, *popt), 'r-', label='Gaussian fit')
        ax.plot((popt[1] - (fwhm / 2), popt[1] + (fwhm / 2)), (popt[0] / 2, popt[0] / 2), color='black', label=f"FWHM ({fwhm:.2f} mV)")
        ax.axvline(x=popt[1] - (fwhm / 2), color="tab:orange", ls="--")
        ax.axvline(x=popt[1] + (fwhm / 2), color="tab:orange", ls="--")

        ax.set_xlim(x_min, x_max)

        ax.set_xlabel('Transit time [ns]')
        ax.set_ylabel('Counts')
        ax.legend()

        ax.set_title(f"TTS for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")

        figname = f"{self.filename[:-5]}-TTS_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5],  "transit-times")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), dpi = 300)
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()



############----------------------------------------################
############----------------------------------------################
############----------------------------------------################
############----------------------------------------################
############----------------------------------------################



class DCS_Measurement:

    # class designed to handle a DCS measurement ( n x m samples taken)

    def __init__(self,
                 signal_data=np.array([]),
                 time_data=np.array([]),
                 metadict=None,
                 filename=None,
                 filepath=None,
                 hdf5_key=None,
                 pmt_id  =None):

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")

        self.filtered_by_threshold = False

        self.default_metadict = {
                "pmt_id":                   -1,
                "time":                     -1,
                "theta [°]":                -1,
                "phi [°]":                  -1,
                "HV [V]":                   -1,
                "Dy10 [V]":                 -1,
                "Laser satus":              -1,
                "Powermeter [pW]":          -1,
                "Picoamp [nA]":             -1,
                "darkbox temp [°C]":        -1,
                "sgnl threshold [mV]":      -1,
                "measurement time [s]":     -1,
                "dark counts":              -1,
                "dark rate [Hz]":           -1,
                }

        self.metadict  = self.default_metadict

        if signal_data.size or time_data.size:
            self.setData(signal=signal_data, time=time_data)

        if metadict:
            self.setMetadict(metadict)

        self.setFilename(filename)
        self.setFilepath(filepath)
        self.setHDF5_key(hdf5_key)
        self.setPMT_ID(pmt_id)

###-----------------------------------------------------------------

    def setData(self, signal = np.array([]), time = np.array([])):
        if signal.size and time.size:
            assert signal.size == time.size
            self.signal = np.array(signal)
            self.time   = np.array(time)
        else: raise Exception("ERROR: either waveforms or signal, trigger and time arrays need to be handed over")

    def getSignal(self):
        return self.signal
    
    def getTime(self):
        return self.time

    def setMetadict(self, metadict):
        if not metadict: return # check for None
        self.metadict = metadict
        for key in self.default_metadict:
            if key not in self.metadict.keys():
                self.metadict[key] = self.default_metadict[key]

    def getMetadict(self):
        return self.metadict

    def setFilename(self, filename):
        self.filename = filename

    def getFilename(self):
        return self.filename

    def setFilepath(self, filepath):
        self.filepath = filepath

    def getFilepath(self):
        return self.filepath

    def setHDF5_key(self, key):
        self.hdf5_key = key

    def getHDF5_Key(self):
        return self.hdf5_key

    def setPMT_ID(self, pmt_id):
        self.pmt_id = pmt_id

    def getPMT_ID(self):
        if self.pmt_id:     return self.pmt_id
        elif self.filepath: return os.path.basename(self.filepath)
        else:               return None

###-----------------------------------------------------------------

    def __len__(self):
        return len(self.signal)

###-----------------------------------------------------------------

    def get_baseline_mean(self):
        return np.mean(self.signal), np.std(self.signal)


    def subtract_baseline(self, baseline=None):
        if not self.signal: self.logger.warning("subtracting baseline without having signal stored!")
        if baseline == None:
            baseline = self.get_baseline_mean()
        self.signal = self.signal - baseline


    def get_darkcounts(self, signal_threshold):
        peaks, _ = find_peaks(-self.signal.flatten(), height=-signal_threshold)
        return len(peaks)
    

    def get_measurement_time(self):
        return self.time[:,-1].sum() / 1_000_000_000 # convert ns -> s


    def measure_metadict(self, signal_threshold):

        meta_dict = {
            "pmt_id":                 self.getPMT_ID() if self.getPMT_ID() else -1,
            "time":                   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "theta [°]":              round( Rotation.Instance().get_position()[1],     3),
            "phi [°]":                round( Rotation.Instance().get_position()[0],     3),
            "Dy10 [V]":               round( uBase.Instance().getDy10(),                3),
            "Powermeter [pW]":        round( Powermeter.Instance().get_power() * 1e12,  3),
            "Laser satus":            Laser.Instance().get_ld()                           ,
            "sgnl threshold [mV]":    round( signal_threshold,                          3)
            }
                
        meta_dict["measurement time [s]"]  = round(self.get_measurement_time(), 6)
        meta_dict["dark counts"]           = self.get_darkcounts(signal_threshold)
        meta_dict["dark rate [Hz]"]        = meta_dict["dark counts"] / meta_dict["measurement time [s]"]

        self.setMetadict(meta_dict)

        return meta_dict

###-----------------------------------------------------------------

    def write_to_file(self, hdf5_connection=None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'a')
            close_on_end = True

        h5_key = self.hdf5_key if self.hdf5_key else f"HV{self.metadict['Dy10 [V]']}/theta{self.metadict['theta [°]']}/phi{self.metadict['phi [°]']}"

        dataset = hdf5_connection.create_dataset(f"{h5_key}/dataset",
                                                 (self.signal.shape[0], self.signal.shape[1], 2),
                                                 dtype=np.float32,
                                                 compression="gzip",
                                                 compression_opts=6)

        dataset[:,:,0] = self.time
        dataset[:,:,1] = self.signal

        for key in self.metadict:
            dataset.attrs[key] = self.metadict[key]

        if close_on_end:
            hdf5_connection.close()


    def read_from_file(self, hdf5_connection=None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'r')
            close_on_end = True

        dataset = hdf5_connection[self.hdf5_key]["dataset"]

        metadict = {}
        for key in dataset.attrs.keys():
            metadict[key] = dataset.attrs[key]
        self.setMetadict(metadict)

        self.setData(time=dataset[:,:,0], signal=dataset[:,:,1])

        if close_on_end:
            hdf5_connection.close()
    

    def read_metadict_from_file(self, hdf5_connection = None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'r')
            close_on_end = True

        dataset = hdf5_connection[self.hdf5_key]["dataset"]

        metadict = {}
        for key in dataset.attrs.keys():
            metadict[key] = dataset.attrs[key]
        self.setMetadict(metadict)

        if close_on_end:
            hdf5_connection.close()


    def clear(self):

        # clears the data (in an attempt to use less memory when not needed)

        del self.time
        del self.signal

    ###-----------------------------------------------------------------


    def plot_peaks(self, signal_threshold, how_many=10):

        flat_signal = self.signal.flatten()
        peak_indices, _ = find_peaks(-flat_signal, height=-signal_threshold)

        fig, ax = plt.subplots()

        cmap    = plt.cm.viridis
        colors  = cmap(np.linspace(0, 0.7, how_many))

        for idx, c in zip(peak_indices, colors):
            start_idx = max(0, idx - 150)
            end_idx = min(len(flat_signal), idx + 150)
            range = end_idx - start_idx
            ax.plot(self.time[0][0:range], flat_signal[start_idx:end_idx], color=c)
        
        # set axis labels and title
        ax.set_xlabel('Time')
        ax.set_ylabel('Amplitude [mV]')

        ax.set_title(f"Dark noise peaks for Dy10={self.metadict['Dy10 [V]']}V")

        figname = f"{self.filename[:-5]}-noise_peaks_Dy10={self.metadict['Dy10 [V]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5],  f"peaks")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()

    def plot_average_peak(self, signal_threshold):

        flat_signal = self.signal.flatten()
        peak_indices, _ = find_peaks(-flat_signal, height=-signal_threshold)

        amplitudes = []
        for idx in peak_indices:
            start_idx = max(0, idx - 150)
            end_idx = min(len(flat_signal), idx + 150)
            amplitudes.append(flat_signal[start_idx:end_idx])

        peak_amplitudes = np.vstack(amplitudes)
        average_peak = np.mean(peak_amplitudes, axis=0)

        fig, ax = plt.subplots()

        ax.plot(self.time[0][0:len(average_peak)], average_peak)

        # set axis labels and title
        ax.set_xlabel('Time')
        ax.set_ylabel('Amplitude [mV]')

        ax.set_title(f"average dark noise peak for Dy10={self.metadict['Dy10 [V]']}V")

        figname = f"{self.filename[:-5]}-average-noise_peak_Dy10={self.metadict['Dy10 [V]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5], f"peaks")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_peak_time_hist(self, signal_threshold, nr_bins=None):

        flat_signal = self.signal.flatten()
        peak_indices, _ = find_peaks(-flat_signal, height=-signal_threshold)

        peak_diffs = np.diff(peak_indices)
        timebase = np.diff(self.time[0])[0]
        data = peak_diffs * timebase

        if not nr_bins:
            nr_bins = max(int(len(data) / 100), 10)

        fig, ax = plt.subplots()

        ax.hist(data, bins=nr_bins, histtype='step', log=True, linewidth=2.0)

        # set axis labels and title
        ax.set_xlabel('relative time from peak to peak [ns]')
        ax.set_ylabel('Counts')

        ax.set_title(f"relative time difference between dark noise peaks Dy10={self.metadict['Dy10 [V]']}V")

        figname = f"{self.filename[:-5]}-noise-time-peaks_Dy10={self.metadict['Dy10 [V]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5], f"histograms")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_amplitude_hist(self, nr_bins =None):

        data = self.signal.flatten()

        if not nr_bins:
            nr_bins = max(int(len(data) / 100), 10)
 
        fig, ax = plt.subplots()

        ax.hist(data, bins=nr_bins, histtype='step', log=True, linewidth=2.0)

        ax.set_xlabel('Amplitude [mV]')
        ax.set_ylabel('Counts')

        ax.set_title(f"Dark noise amplitudes for Dy10={self.metadict['Dy10 [V]']}V")

        figname = f"{self.filename[:-5]}-noise_amplitude_Dy10={self.metadict['Dy10 [V]']}.png"
        save_dir = os.path.join(self.filepath, self.filename[:-5],  f"histograms")
        os.makedirs(save_dir, exist_ok=True)
        fig.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()