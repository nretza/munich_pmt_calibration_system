#!/usr/bin/python3

import os
import logging
import h5py
import numpy as np
from scipy import constants
from matplotlib import pyplot as plt

import config

from devices.Laser import Laser
from devices.uBase import uBase
from devices.Rotation import Rotation
from devices.Powermeter import Powermeter


class Waveform:

    # class to handle a single Waveform

    def __init__(self, time, signal, trigger):

        assert len(time) == len(signal)
        assert len(time) == len(trigger)
        
        self.time    = np.array(time)
        self.signal  = np.array(signal)
        self.trigger = np.array(trigger)

        self.trigger_val = 1

    @property
    def mean(self):
        return np.mean(self.signal)

    @property
    def min_value(self):
        return np.min(self.signal)

    @property
    def min_time(self):
        return self.time[np.argmin(self.signal)]

    @property
    def trigger_time(self):
        trigger_index = np.flatnonzero((self.trigger[:-1] < self.trigger_val) & (self.trigger[1:] > self.trigger_val))+1
        return self.time[trigger_index[0]]

    @property
    def tt(self):
        return self.min_time - self.trigger_time

###-----------------------------------------------------------------

    def __eq__(self, other):
        return self.time == other.time and self.signal == other.signal and self.trigger == other.trigger

    def __len__(self):
        return len(self.time)

###-----------------------------------------------------------------

    def subtract_baseline(self, value):

        self.signal -= value
        return self.signal

    def calculate_gain(self):

        if hasattr(self, "gain"): return self.gain

        # expected transit time
        expected_tt_max = 220
        expected_tt_min = 190
        expected_waveform_length = 20

        # get relevant part out of total waveform
        if (self.min_time > self.trigger_time + expected_tt_min) and (self.min_time < self.trigger_time + expected_tt_max):
            mask = (self.time > self.min_time - expected_waveform_length) & (self.time < self.min_time + expected_waveform_length)
        else:
            mask = (self.time > expected_tt_min) & (self.time < expected_tt_max)
    
        # calculate area and gain
        area = np.trapz(self.signal[mask]*1e-3, self.time[mask]*1e-9)
        self.charge = area/50
        self.gain = abs(self.charge)/constants.e
        return self.gain
    
    def calculate_charge(self):
        self.calculate_gain()
        return self.charge


###-----------------------------------------------------------------
###-----------------------------------------------------------------
###-----------------------------------------------------------------



class Measurement:

    # class designed to handle a meassurement (multiple waveforms taken in bulk)

    def __init__(self, waveform_list=None, signal_data=None, trigger_data=None, time_data = None, metadict=None, filename=None, filepath=None, hdf5_key=None):

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")

        self.filtered_by_threshold = False

        self.default_metadict = {
                "theta":            -1,
                "phi":              -1,
                "HV":               -1,
                "Dy10":             -1,
                "Powermeter":       -1,
                "Laser temp":       -1,
                "Laser tune":       -1,
                "Laser freq":       -1,
                "sgnl_threshold":   -1,
                "occ":              -1,
                "gain":             -1,
                "time":             -1,
                }

        if waveform_list or (signal_data and trigger_data and time_data): self.setWaveforms(waveforms = waveform_list, signal=signal_data, trigger=trigger_data, time=time_data)
        if metadict: self.setMetadict(metadict)
        if filename: self.setFilename(filename)
        if filepath: self.setFilepath(filepath)
        if hdf5_key: self.setHDF5_key(hdf5_key)

###-----------------------------------------------------------------

    def setWaveforms(self, waveforms = None, signal = None, trigger = None, time = None):
        if waveforms:
            if signal or trigger or time: self.logger.warning("Both Waveforms and signal arrays handed to data struct. Will only use waveforms!")
            self.waveforms = waveforms
        elif signal and trigger and time:
            self.waveforms = []
            for time, signal, trigger in zip(time, signal, trigger):
                self.waveforms.append(Waveform(time=time, signal=signal, trigger=trigger))
        else: raise Exception("ERROR: either waveforms or signal, trigger and time arrays need to be handed over")

    def getWaveforms(self):
        return self.waveforms

    def setMetadict(self, metadict):
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
        if self.filtered_by_threshold:
            print("WARNING: calculating occupancy on filtered Dataset. Value might be incorrect")
            self.logger.warning("calculating occupancy on filtered Dataset. Value might be incorrect")
        i = 0
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: i +=1
        return float(i)/float(len(self.waveforms))

    def calculate_gain(self, signal_threshold):
        gains = []
        for wf in self.waveforms:
            if wf.min_value < signal_threshold: gains.append(wf.calculate_gain())
        return sum(gains)/len(gains)

    def get_average_wf(self):
        xValues = np.array([wf.time for wf in self.waveforms])
        averageX = np.mean(xValues, axis=0)
        yValues = np.array([wf.signal for wf in self.waveforms])
        averageY = np.mean(yValues, axis=0)
        return (averageX, averageY)
    
    def get_baseline_mean(self):
        means = [wf.mean for wf in self.waveforms]
        return np.mean(means), np.std(means)

    def subtract_baseline(self, baseline=None):
        if baseline == None:
            baseline = self.get_baseline_mean()
        for wf in self.waveforms:
            wf.subtract_baseline(baseline[0])

    def filter_by_threshold(self, signal_threshold):
        for wf in self.waveforms:
            if wf.min > signal_threshold:
                self.waveforms.remove(wf)
        self.filtered_by_threshold = True

    def meassure_metadict(self, signal_threshold):

        meta_dict = {
            "theta":            round( Rotation.Instance().get_position()[1], 2),
            "phi":              round( Rotation.Instance().get_position()[0], 2),
            "Dy10":   	        round( uBase.Instance().getDy10(), 2),
            "Powermeter":       round( Powermeter.Instance().get_power(), 2),
            "Laser temp":       round( Laser.Instance().get_temp(), 2),
            "Laser tune":       round( Laser.Instance().get_tune_value()/10, 2),
            "Laser freq":       round( Laser.Instance().get_freq(), 2),
            "sgnl_threshold" :  round( signal_threshold, 2),
            }
                
        meta_dict["occ"] = round(self.calculate_occ(signal_threshold),  3)
        meta_dict["gain"] = round(self.calculate_gain(signal_threshold),  2)

        self.setMetadict(meta_dict)

        return meta_dict

###-----------------------------------------------------------------

    def write_to_file(self, hdf5_connection=None):

        close_on_end = False
        if not hdf5_connection:
            hdf5_connection = h5py.File(os.path.join(self.filepath,self.filename), 'a')
            close_on_end = True

        key = self.hdf5_key if self.hdf5_key else f"theta{self.metadict['theta']}/phi{self.metadict['phi']}"
        dataset = hdf5_connection.create_dataset(f"{key}/dataset", (len(self.waveforms), len(self.waveforms[0].time), 3), 'f')

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

        self.setWaveforms(time=dataset[0], signal=dataset[1], trigger=dataset[2])

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

###-----------------------------------------------------------------

    def plot_wfs(self):
        pass

    def plot_peaks(self):
        pass
    
    def plot_wf_masks(self):
        pass

    def plot_average_wfs(self):
        pass

    def plot_hist(self):
        pass

    def plot_transit_times(self):
        pass
    
    def plot_dark_count_rate(self):
        pass



###-----------------------------------------------------------------
###-----------------------------------------------------------------
###-----------------------------------------------------------------


class data_handler:

    # class to handle all measurements of a given testing procedure
    # only used for data analysis (-> data extracted from hdf5)

    def __init__(self, filename, filepath):
        self.filename = filename
        self.filepath = filepath

        self.data_loaded = False
        self.metadicts_loaded = False

        self.meassurements = []

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for key in self.get_all_keys(h5):
                try:
                    _ = h5[key]["dataset"]
                except:
                    continue
                self.meassurements.append(Measurement(filename=filename, filepath=filepath, hdf5_key=key))

###-----------------------------------------------------------------

    # loading functions are called by plotting on demand. No need to call them manually
    
    def get_all_keys(self, h5):
        keys = []
        h5.visit(lambda key: keys.append(key) if isinstance(h5[key], h5py.Group) else None)
        return keys

    def load_metadicts(self):

        # loads only metadicts to reduce memory usage

        if self.metadicts_loaded:
            return

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:
            for data in self.meassurements: data.read_metadict_from_file(hdf5_connection=h5)

        self.metadicts_loaded = True

    def load_data(self):

        # load full data set (heavy on memory!)

        if self.data_loaded:
            return

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:
            for data in self.meassurements: data.read_from_file(hdf5_connection=h5)

        self.data_loaded = True

###-----------------------------------------------------------------

    def plot_angular_acceptance(self):
    
        # load data
        self.load_metadicts()

        occ_list = []
        theta_list = []
        for data in self.meassurements:
            occ_list.append(data.getMetadict["occ"])
            theta_list.append(data.getMetadict["theta"])
        occ_max = max(occ_list)
        occ_list = [i / occ_max for i in occ_list]
        plt.figure()
        plt.scatter(np.array(theta_list), np.array(occ_list))
        plt.xlabel('theta')
        plt.ylabel('relative angular acceptance')
        plt.title(f"relative angular acceptance from theta={min(theta_list)} to theta={max(theta_list)}")
        figname = f"{self.filename[:-5]}-angular acceptance.png"
        save_dir = os.path.join(self.filepath, "angular acceptance")
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')

    def plot_wfs(self):
        pass

    def plot_peaks(self):
        pass
    
    def plot_wf_masks(self):
        pass

    def plot_average_wfs(self):
        pass

    def plot_hist(self):
        pass

    def plot_transit_times(self):
        pass

    def plot_dark_count_rate(self):
        pass