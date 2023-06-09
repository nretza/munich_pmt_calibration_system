#!/usr/bin/python3

import config
import numpy as np
from matplotlib import pyplot as plt
from scipy import constants


class Waveform:

    # class to handle a single Waveform

    def __init__(self, time, signal, trigger, signal_threshold = -4):
        
        self.time    = np.array(time, dtype=np.float32)
        self.signal  = np.array(signal, dtype=np.float32)
        self.trigger = np.array(trigger, dtype=np.float32)

        assert len(self.time) == len(self.signal)
        assert len(self.time) == len(self.trigger)

        self.trigger_val = 2000
        self.default_trigger_index = 100
        self.signal_threshold = signal_threshold

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
    def has_signal(self):
        if self.signal_threshold: return self.min_value < self.signal_threshold
        else: return True

    @property
    def threshold_crossing_time(self):
        return self.time[np.argmax(self.signal < self.signal_threshold)]

    @property
    def trigger_time(self):
        try:
            trigger_index = np.flatnonzero((self.trigger[:-1] < self.trigger_val) & (self.trigger[1:] > self.trigger_val))[0]
        except:
            trigger_index = self.default_trigger_index
        return self.time[trigger_index]

    @property
    def transit_time(self):
        return self.min_time - self.trigger_time

    @property
    def rise_time(self):
        return self.min_time - self.threshold_crossing_time

    @property
    def mask(self):

        # expected transit time
        expected_tt_max = 220
        expected_tt_min = 190
        expected_waveform_length = 20

        # get relevant part out of total waveform
        if (self.min_time > self.trigger_time + expected_tt_min) and (self.min_time < self.trigger_time + expected_tt_max):
            mask = (self.time > self.min_time - expected_waveform_length) & (self.time < self.min_time + expected_waveform_length)
        else:
            mask = (self.time > expected_tt_min) & (self.time < expected_tt_max)
        
        return mask

###-----------------------------------------------------------------

    def __eq__(self, other):
        return np.array_equal(self.time, other.time) and np.array_equal(self.signal, other.signal) and np.array_equal(self.trigger, other.trigger)

    def __len__(self):
        return len(self.time)

###-----------------------------------------------------------------

    def subtract_baseline(self, value):

        self.signal -= value
        return self.signal


    def calculate_gain(self):

        if hasattr(self, "gain"): return self.gain
    
        # TODO: Review this

        # calculate area and gain
        area = np.trapz(self.signal[self.mask]*1e-3, self.time[self.mask]*1e-9)
        self.charge = area/50 # 50 Ohm termination at scope
        self.gain = abs(self.charge)/constants.e
        return self.gain
    

    def calculate_charge(self):
        self.calculate_gain()
        return self.charge


    def has_prepulse(self):
        pass


    def has_ringing(self):
        pass
    
###-----------------------------------------------------------------

    def plot(self, out_file):

        plt.figure()
        plt.plot(self.time, self.signal)
        plt.xlabel('time [ns]')
        plt.ylabel('Voltage [mV]')
        plt.title(f"single Waveform")
        plt.vlines([self.trigger_time], label="trigger time", colors=["tab:red"], linestyles="dasheed")
        plt.savefig(out_file)
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()
