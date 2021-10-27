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

    def filter_sph_and_set_data_to_SI(self, filename='./data/PMT001/test_with_attr'):

        with h5py.File(filename, 'r') as f:
            for arr in f:  #TODO: add
                pass