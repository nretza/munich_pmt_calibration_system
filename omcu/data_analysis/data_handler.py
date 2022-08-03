#!/usr/bin/python3

import os
import h5py
from data_analysis.data_struct import data_struct

#TODO: logging, printouts, other analysis

class data_handler:

    def __init__(self, filename, filepath):
        self.filename = filename
        self.filepath = filepath
        self.load_data()

    def get_all_keys(self, h5):
        keys = []
        h5.visit(lambda key: keys.append(key) if isinstance(h5[key], h5py.Group) else None)
        return keys
    
    def load_data(self):

        h5 = h5py.File(os.path.join(self.filepath, self.filename), "r")
        self.data_list=[]
        for key in self.get_all_keys(h5):
            try:
                signl = h5[key]["signal"]
                trgr  = h5[key]["trigger"]
            except:
                continue
            metadict = {}
            for key in signl.attrs.keys():
                metadict[key] = signl.attrs[key]

            self.data_list.append(data_struct(signl, trgr, metadict, self.filename, self.filepath))

    def plot_wfs(self, number=10, threshold=-3):
        for data in self.data_list:
            data.plot_wfs(number=number, threshold=threshold)
    
    def plot_peaks(self, ratio=0.33, width=2):
        for data in self.data_list:
            data.plot_peaks(ratio=ratio, width=width)

    def plot_wfs_mask(self, number=10, threshold=-3):
        for data in self.data_list:
            data.plot_wfs_mask(number=number, threshold=threshold)

    def plot_average_wf(self):
        for data in self.data_list:
            data.plot_average_wf()

    def plot_hist(self, mode="amplitude",exclude=['900', '1300']):
        for data in self.data_list:
            data.plot_hist(mode=mode, exclude=exclude)
    
    def plot_transit_times(self, binsize=0.4):
        for data in self.data_list:
            data.plot_transit_times(binsize=binsize)

    def plot_dark_count_rate(self):
        for data in self.data_list:
            data.get_dark_count_rate()
        pass

    def plot_angluar_acceptance():
        pass