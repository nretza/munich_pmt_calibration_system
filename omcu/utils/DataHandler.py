#!/usr/bin/python3

import logging
import os

import config
import h5py
import numpy as np
from matplotlib import pyplot as plt
from utils.Measurement import Measurement


class DataHandler:

    # class to handle all measurements of a given testing procedure
    # only used for data analysis (-or data analysis (-> data extracted from hdf5)

    def __init__(self, filename, filepath):

        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")

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


    def load_all_data(self):

        # load full data set (heavy on memory!)

        if self.data_loaded:
            return

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:
            for data in self.meassurements: data.read_from_file(hdf5_connection=h5)

        self.data_loaded = True

###-----------------------------------------------------------------

    # TODO plotting

    # plotting behavour depents on the type of measurement (PCS, FHVS...).
    # One should call only those functions that correspond to the desired measurement the datahandler has its data from

    def plot_angular_acceptance(self):
    
        # load data
        self.load_metadicts()

        occ_list = []
        theta_list = []
        for data in self.meassurements:
            occ_list.append(data.metadict["occ [%]"])
            theta_list.append(data.metadict["theta [°]"])
        occ_max = max(occ_list)
        occ_list = [i / occ_max for i in occ_list]

        plt.figure()

        plt.scatter(np.array(theta_list), np.array(occ_list))

        plt.xlabel('theta [°]')
        plt.ylabel('relative angular acceptance')

        plt.title(f"relative angular acceptance from theta={min(theta_list)}° to theta={max(theta_list)}°")
        figname = f"{self.filename[:-5]}-angular acceptance.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_angle_to_gain(self):

        # load data
        self.load_metadicts()

        gain_list = []
        teta_list = []
        for data in self.meassurements:
            gain_list.append(data.metadict["gain"])
            teta_list.append(data.metadict["theta [°]"])

        plt.figure()

        plt.scatter(np.array(teta_list), np.array(gain_list))

        plt.xlabel('theta [°]')
        plt.ylabel('gain')

        plt.title(f"average gain from theta={min(teta_list)}° to theta={max(teta_list)}°")
        figname = f"{self.filename[:-5]}-angle_to_gain.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_angle_to_TTS(self):
        
        # load data
        self.load_metadicts()

        tts_list = []
        theta_list = []
        for data in self.meassurements:
            tts_list.append(data.metadict["transit time spread [ns]"])
            theta_list.append(data.metadict["theta [°]"])

        plt.figure()

        plt.scatter(np.array(theta_list), np.array(tts_list))

        plt.xlabel('theta [°]')
        plt.ylabel('transit time spread [ns]')

        plt.title(f"transit time spread from theta={min(theta_list)}° to theta={max(theta_list)}°")
        figname = f"{self.filename[:-5]}-angle_to_TTS.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_angle_to_rise_time(self):

        # load data
        self.load_metadicts()

        rise_time_list = []
        theta_list = []
        for data in self.meassurements:
            rise_time_list.append(data.metadict["rise time [ns]"])
            theta_list.append(data.metadict["theta [°]"])

        plt.figure()

        plt.scatter(np.array(theta_list), np.array(rise_time_list))

        plt.xlabel('theta [°]')
        plt.ylabel('rise time [ns]')

        plt.title(f"rise time from theta={min(theta_list)}° to theta={max(theta_list)}°")
        figname = f"{self.filename[:-5]}-angle_to_rise_time.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_HV_to_gain(self):

        # load data
        self.load_metadicts()

        gain_list = []
        HV_list = []
        for data in self.meassurements:
            gain_list.append(data.metadict["gain"])
            HV_list.append(data.metadict["Dy10 [V]"])

        plt.figure()

        plt.scatter(np.array(HV_list), np.array(gain_list))

        plt.xlabel('Dy10 [V]')
        plt.ylabel('gain')

        plt.title(f"average gain from Dy10={min(HV_list)} V to Dy10={max(HV_list)} V")
        figname = f"{self.filename[:-5]}-HV_to_gain.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_HV_to_TTS(self):

        # load data
        self.load_metadicts()

        tts_list = []
        HV_list = []
        for data in self.meassurements:
            tts_list.append(data.metadict["transit time spread [ns]"])
            HV_list.append(data.metadict["Dy10 [V]"])

        plt.figure()

        plt.scatter(np.array(HV_list), np.array(tts_list))

        plt.xlabel('Dy10 [V]')
        plt.ylabel('transit time spread [V]')

        plt.title(f"transit time spread from Dy10={min(HV_list)} V to Dy10={max(HV_list)} V")
        figname = f"{self.filename[:-5]}-HV_to_TTS.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_HV_to_rise_time(self):
        
        # load data
        self.load_metadicts()

        rise_time_list = []
        HV_list = []
        for data in self.meassurements:
            rise_time_list.append(data.metadict["rise time [ns]"])
            HV_list.append(data.metadict["Dy10 [V]"])

        plt.figure()

        plt.scatter(np.array(HV_list), np.array(rise_time_list))

        plt.xlabel('Dy10 [V]')
        plt.ylabel('rise time [ns]')

        plt.title(f"rise time from Dy10={min(HV_list)} V to Dy10={max(HV_list)} V")
        figname = f"{self.filename[:-5]}-HV_to_rise_time.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_laser_tune_to_charge(self):
        
        # load data
        self.load_metadicts()

        laser_tune_list = []
        charge_list = []
        for data in self.meassurements:
            laser_tune_list.append(data.metadict["laser tune [%]"])
            charge_list.append(data.metadict["charge [pC]"])

        plt.figure()

        plt.scatter(np.array(laser_tune_list), np.array(charge_list))

        plt.xlabel('laser tune [%]')
        plt.ylabel('charge [pC]')

        plt.title(f"charge from laser_tune={min(charge_list)}% to laser_tune={max(charge_list)}%")
        figname = f"{self.filename[:-5]}-laser_tune_to_charge.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.close('all')


    def plot_HV_to_dark_count(self):
        pass

###-----------------------------------------------------------------

    # plotting of Measurement-plots

    def plot_wfs(self, how_many=10):

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)
                data.plot_wfs(how_many)
                if clear: data.clear()
                

    def plot_peaks(self, ratio=0.33, width=2):
        
        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)
                data.plot_peaks(ratio, width)
                if clear: data.clear()

    
    def plot_wf_masks(self, how_many=10):
        
        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)
                data.plot_wf_masks(how_many)
                if clear: data.clear()

    def plot_average_wfs(self):
        
        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)
                data.plot_average_wfs()
                if clear: data.clear()
                

    def plot_hist(self, mode="amplitude"):

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)

                data.plot_hist(mode)
                if clear: data.clear()


    def plot_transit_times(self, binsize = 0.4):

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)

                data.plot_transit_times(binsize)
                if clear: data.clear()