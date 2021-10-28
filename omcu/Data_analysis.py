#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

from submodules.Picoscope import Picoscope
import matplotlib.pyplot as plt
import numpy as np
from numpy import trapz
import scipy.constants as const
import h5py

class Analysis:

    def __init__(self):

        Ps = Picoscope()
        self.nSamples = Ps.get_nSamples()

    def filter_sph(self, filename='./data/PMT001/20211028-111907/PMT001.hdf5', threshold=-4):

        h5 = h5py.File(filename, 'r+')
        for key in h5.keys():
            for key2 in h5[key]:
                dataset = h5[key][key2]['signal']
                dataset.attrs['Passes threshold'] = np.zeros((len(dataset)))
                for i, wf in enumerate(dataset):
                    minval = np.min(wf)
                    if minval < threshold:
                        dataset.attrs['Passes threshold'][i] = 1  #TODO: fix

