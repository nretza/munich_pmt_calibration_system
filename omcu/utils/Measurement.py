#!/usr/bin/python3

import logging
import math
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
from utils.Waveform import Waveform


#placed here to avoid circular imports
def gaussian(x, a, mu, sigma):
    return a * np.exp(- (x - mu) ** 2 / (sigma ** 2))


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
                 hdf5_key=None):

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")

        self.filtered_by_threshold = False

        self.default_metadict = {
                "time":                     -1,
                "theta [°]":                -1,
                "phi [°]":                  -1,
                "HV [V]":                   -1,
                "Dy10 [V]":                 -1,
                "Powermeter [pW]":          -1,
                "Picoamp [nA]":             -1,
                "Laser temp [°C]":          -1,
                "Laser tune [%]":           -1,
                "Laser pulse freq [Hz]":    -1,
                "Laser wavelength [nm]":    -1,
                "darkbox temp [°C]":        -1,
                "sgnl threshold [mV]":      -1,
                "occ [%]":                  -1,
                "avg amplitude [mV]":       -1,
                "std amplitude [mV]":       -1,
                "gain":                     -1,
                "gain spread":              -1,
                "charge [pC]":              -1,
                "charge spread [pC]":       -1,
                "rise time [ns]":           -1,
                "rise time spread [ns]":    -1,
                "transit time [ns]":        -1,
                "transit time spread [ns]": -1,
                "dark count [Hz]":          -1,
                "ringing":                  -1,
                "pre pulse":                -1,
                "post pulse":               -1
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
        return np.mean(amplitudes), np.std(amplitudes)


    def calculate_gain(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating gain without having Waveforms stored!")
        gains = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold:
                gains = np.append(gains, wf.calculate_gain())
        if len(gains) == 0: return 0,0
        return np.mean(gains), np.std(gains)


    def validate_gain(self, delta=10):
        return (self.metadict["gain"] - self.calculate_gain(self.metadict["sgnl_threshold"])) < delta


    def calculate_charge(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating charge without having Waveforms stored!")
        charges = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: charges = np.append(charges, wf.calculate_charge())
        return np.mean(charges), np.std(charges)


    def calculate_rise_time(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating rise time without having Waveforms stored!")
        rise_times = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: rise_times = np.append(rise_times, wf.rise_time)
        return np.mean(rise_times), np.std(rise_times)


    def calculate_transit_time(self, signal_threshold):
        if not self.waveforms: self.logger.warning("calculating transit time without having Waveforms stored!")
        transit_times = np.array([])
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: transit_times = np.append(transit_times, wf.transit_time)
        return np.mean(transit_times), np.std(transit_times)


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
        return np.mean(means), np.std(means)


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


    def meassure_metadict(self, signal_threshold):

        meta_dict = {
            "time":                   datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
            "theta [°]":              round( Rotation.Instance().get_position()[1],     2),
            "phi [°]":                round( Rotation.Instance().get_position()[0],     2),
            "Dy10 [V]":               round( uBase.Instance().getDy10(),                2),
            "Powermeter [pW]":        round( Powermeter.Instance().get_power() * 1e12,  3),
            "Laser temp [°C]":        round( Laser.Instance().get_temp(),               2),
            "Laser tune [%]":         round( Laser.Instance().get_tune_value()/10,      2),
            "Laser pulse freq [Hz]":  round( Laser.Instance().get_freq(),               2),
            "sgnl threshold [mV]":    round( signal_threshold,                          2)
            }
                
        meta_dict["occ [%]"]                  = round(self.calculate_occ(signal_threshold),                3)
        meta_dict["avg amplitude [mV]"]       = round(self.calculate_avg_amplitude(signal_threshold)[0],   3)
        meta_dict["std amplitude [mV]"]       = round(self.calculate_avg_amplitude(signal_threshold)[1],   3)
        meta_dict["gain"]                     = round(self.calculate_gain(signal_threshold)[0],            3)
        meta_dict["gain spread"]              = round(self.calculate_gain(signal_threshold)[1],            3)
        meta_dict["charge [pC]"]              = round(self.calculate_charge(signal_threshold)[0] * 1e12,   3)
        meta_dict["charge spread [pC]"]       = round(self.calculate_charge(signal_threshold)[1] * 1e12,   3)
        meta_dict["rise time [ns]"]           = round(self.calculate_rise_time(signal_threshold)[0],       3)
        meta_dict["rise time spread [ns]"]    = round(self.calculate_rise_time(signal_threshold)[1],       3)
        meta_dict["transit time [ns]"]        = round(self.calculate_transit_time(signal_threshold)[0],    3)
        meta_dict["transit time spread [ns]"] = round(self.calculate_transit_time(signal_threshold)[1],    3)

        self.setMetadict(meta_dict)

        return meta_dict

###-----------------------------------------------------------------

    def write_to_file(self, hdf5_connection=None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'a')
            close_on_end = True

        h5_key = self.hdf5_key if self.hdf5_key else f"HV{self.metadict['Dy10 [V]']}/theta{self.metadict['theta [°]']}/phi{self.metadict['phi [°]']}"
        dataset = hdf5_connection.create_dataset(f"{h5_key}/dataset", (len(self.waveforms), len(self.waveforms[0].time), 3), 'f')

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

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, how_many)))

        plt.figure()

        for wf, c in zip(self.waveforms, colors): plt.plot(wf.time, wf.signal, color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')

        plt.axvline(x=self.waveforms[0].trigger_time, color='black', ls=":", label="trigger time")
        plt.legend()

        plt.title(f"Waveforms for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        figname = f"{self.filename[:-5]}-waveforms_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5],  "waveforms")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_peaks(self, ratio=0.33, width=2, how_many=10):

        if not self.waveforms:
            print("plotting waveform peaks without having Waveforms stored!")
            return

        average_wf = self.get_average_wf()
        threshold = np.min(average_wf[1]) * ratio

        plt.figure()
        
        for i in range(how_many):
            wf = self.waveforms[i]
            peaks = find_peaks(-wf.signal, height=-threshold, width=width)
            l = len(peaks[0])
            color = "yellow" if l == 0 else "green"
            plt.plot(wf.time, wf.signal, color)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')

        plt.axvline(x=self.waveforms[0].trigger_time, color='black', ls=":", label="trigger time")
        plt.axhline(y=threshold, color='red', linestyle='--')

        plt.legend()

        plt.title(f"Waveform Peaks for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        figname = f"{self.filename[:-5]}-waveform_peaks_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5],  "waveform-peaks")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_wf_masks(self, how_many=10):

        if not self.waveforms:
            print("plotting waveform masks without having Waveforms stored!")
            return

        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, how_many)))
        plt.figure()

        for wf, c in zip(self.waveforms, colors):
                plt.plot(wf.time[wf.mask], wf.signal[wf.mask], color=c)

        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')

        plt.axvline(x=self.waveforms[0].trigger_time, color='black', ls=":", label="trigger time")

        plt.legend()

        plt.title(f"Waveform Masks for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        figname = f"{self.filename[:-5]}-waveform_masks_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5],  "waveform-masks")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_average_wf(self):

        if not self.waveforms:
            print("plotting average waveforms without having Waveforms stored!")
            return

        average_wf = self.get_average_wf()

        plt.figure()
        plt.plot(average_wf[0], average_wf[1])

        plt.xlabel('Time [ns]')
        plt.ylabel('Voltage [mV]')

        plt.axvline(x=self.waveforms[0].trigger_time, color='black', ls=":", label="trigger time")

        plt.legend()

        plt.title(f"Average Waveform for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        figname = f"{self.filename[:-5]}-average_waveform_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5],  "average-waveform")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def plot_ampl_to_gain(self):

        ampl_list = []
        gain_list = []
        for wf in self.waveforms:
            ampl_list.append(wf.min_value)
            gain_list.append(wf.calculate_gain())

        plt.figure()

        plt.scatter(np.array(ampl_list), np.array(gain_list))

        plt.xlabel("amplitude [mV]")
        plt.ylabel("gain")

        plt.title(f"amplitude to gain correlation")
        figname = f"{self.filename[:-5]}-ampl_to_gain.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "correlations")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def plot_hist(self, mode="amplitude", nr_bins =None):

        # TODO: twin axis for two histograms

        if not self.waveforms:
            print(f"plotting {mode}-histogram without having Waveforms stored!")
            return

        if mode not in ["amplitude", "gain", "charge", "amplitude_all"]:
            return

        fig, ax1 = plt.subplots()

        if mode == "amplitude": data = [wf.min_value for wf in self.waveforms]
        if mode == "gain":      data = [wf.calculate_gain() for wf in self.waveforms]
        if mode == "charge":    data = [wf.calculate_charge() for wf in self.waveforms]
        if mode == "amplitude_all": data = [value for wf in self.waveforms for value in wf.signal]

        if not nr_bins:
            nr_entries = len(data)
            nbins = int(nr_entries / 100)
            if nbins < 10: nbins = 10
        else:
            nbins = nr_bins

        ax1.hist(data, bins=nbins, histtype='step', log=True, linewidth=2.0)

        if mode == "amplitude": ax1.set_xlabel('Amplitude [mV]')
        if mode == "gain":      ax1.set_xlabel('Gain')
        if mode == "charge":    ax1.set_xlabel('Charge')
        if mode == "amplitude_all": ax1.set_xlabel('Amplitude [mV]')

        ax1.set_ylabel('Counts')

        if mode == "amplitude": plt.axvline(x=self.metadict["sgnl threshold [mV]"], color='black', ls=":", label="trigger threshold")
        if mode == "amplitude_all": plt.axvline(x=self.metadict["sgnl threshold [mV]"], color='black', ls=":", label="trigger threshold")

        plt.legend()

        fig.tight_layout()
        plt.title(f"Waveform {mode}s for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        figname = f"{self.filename[:-5]}-hist_{mode}s_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5],  f"{mode}-histograms")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_transit_times(self, nr_bins=100):

        if not self.waveforms:
            print(f"plotting transit times without having Waveforms stored!")
            return

        transit_times = [wf.transit_time for wf in self.waveforms]

        plt.figure()

        plt.hist(transit_times, histtype='step', bins=nr_bins, linewidth=2.0)

        plt.xlabel('Transit time [ns]')
        plt.ylabel('Counts')

        plt.title(f"TTS for Dy10={self.metadict['Dy10 [V]']}V, laser_tune={self.metadict['Laser tune [%]']}, phi={self.metadict['phi [°]']}, theta={self.metadict['theta [°]']}")
        figname = f"{self.filename[:-5]}-TTS_Dy10={self.metadict['Dy10 [V]']}_lasertune={self.metadict['Laser tune [%]']}_phi={self.metadict['phi [°]']}_theta={self.metadict['theta [°]']}.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5],  "transit-times")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')



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
                 hdf5_key=None):

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")

        self.filtered_by_threshold = False

        self.default_metadict = {
                "time":                     -1,
                "theta [°]":                -1,
                "phi [°]":                  -1,
                "HV [V]":                   -1,
                "Dy10 [V]":                 -1,
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

###-----------------------------------------------------------------

    def __len__(self):
        return len(self.waveforms)

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


    def meassure_metadict(self, signal_threshold):

        meta_dict = {
            "time":                   datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
            "theta [°]":              round( Rotation.Instance().get_position()[1],     3),
            "phi [°]":                round( Rotation.Instance().get_position()[0],     3),
            "Dy10 [V]":               round( uBase.Instance().getDy10(),                3),
            "Powermeter [pW]":        round( Powermeter.Instance().get_power() * 1e12,  3),
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
        dataset = hdf5_connection.create_dataset(f"{h5_key}/dataset", (self.signal.shape[0], self.signal.shape[1], 2), 'f')

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


    def plot_amplitude_hist(self, nr_bins =None):

        data = self.signal.flatten()

        if not nr_bins:
            nr_entries = len(data)
            nbins = int(nr_entries / 100)
            if nbins < 10: nbins = 10
        else:
            nbins = nr_bins

        fig, ax1 = plt.subplots()
        ax1.hist(data, bins=nbins, histtype='step', log=True, linewidth=2.0)
        ax1.set_xlabel('Amplitude [mV]')
        ax1.set_ylabel('Counts')

        fig.tight_layout()
        plt.title(f"Dark noise amplitudes for Dy10={self.metadict['Dy10 [V]']}V")
        figname = f"{self.filename[:-5]}-noise_amplitude_Dy10={self.metadict['Dy10 [V]']}.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5],  f"histograms")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname), bbox_inches='tight')
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')