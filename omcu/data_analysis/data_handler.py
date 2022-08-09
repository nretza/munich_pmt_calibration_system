#!/usr/bin/python3

import os
import h5py
from data_analysis.data_struct import data_struct
import matplotlib.pyplot as plt
import numpy as np

import config


#TODO: logging
#TODO: proper charge/gain hist > change current hists
#TODO: implement angular acceptance
#TODO: fix bug in TTS
#TODO: average over all HVs
#TODO: gain/HV dependance
#TODO: dark count rate
#TODO: QE -> change setup


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

    def plot_angluar_acceptance(self):
        occ_list = []
        theta_list = []
        for data in self.data_list:
            occ_list.append(data.metadict["occ"])
            theta_list.append(data.metadict["theta"])
        occ_max = max(occ_list)
        occ_list = [i /occ_max for i in occ_list]

        plt.figure()
        plt.plot(np.array(theta_list), np.array(occ_list))
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
        

    def plot_angular_acceptance2D(self):
        pass

    def plot_average_wf_all_HV(self):
        pass