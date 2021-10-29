#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
import matplotlib.pyplot as plt
import numpy as np
from numpy import trapz
import scipy.constants as const
import h5py
from Waveform import Waveform

#from Data_analysis import Analysis as Al
#data2910 = Al('./data/PMT001/20211029.../PMT001.hdf5')
#data2910.calculate_gain_sph(threshold)

class Analysis:

    def __init__(self, filename='./data/PMT001/20211028-114024/PMT001.hdf5'):
        self.filename = filename
        Ps = Picoscope()
        self.nSamples = Ps.get_nSamples()

    def calculate_gain_sph(self, threshold=-4):

        h5 = h5py.File(self.filename, 'r+')
        wfs = []
        for key in h5.keys():
            for key2 in h5[key]:
                dataset = h5[key][key2]['signal']
                for i, wf in enumerate(dataset):
                    minval = np.min(wf[:,1])
                    if minval < threshold:
                        wf_object = Waveform(key,key2,wf[:,1],wf[:,0])
                        wf_object.calculate_gain()
                        wfs.append(wf_object)

        return wfs

    def plot_hist_gain(self, threshold=-4):

        wf_list = self.calculate_gain_sph(threshold)
