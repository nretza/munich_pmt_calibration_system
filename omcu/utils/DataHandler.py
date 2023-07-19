#!/usr/bin/python3

import logging
import os

import config
import h5py
import numpy as np
from matplotlib import pyplot as plt
from utils.Measurement import Measurement, DCS_Measurement
from scipy import stats


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

        MeasurementType = Measurement if not "DCS" in self.filename else DCS_Measurement

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for key in self.get_all_keys(h5):
                try:
                    _ = h5[key]["dataset"]
                except:
                    continue
                self.meassurements.append(MeasurementType(filename=filename, filepath=filepath, hdf5_key=key))

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

    
    def recalculate_metadicts(self):

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)

                signal_threshold = data.metadict["sgnl threshold [mV]"]
                data.measure_metadict(signal_threshold, only_waveform_characteristics=True)
                if clear: data.clear()

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

        plt.figure()

        plt.scatter(np.array(theta_list), np.array(occ_list))

        plt.xlabel('theta [°]')
        plt.ylabel('occupancy [%]')

        plt.title(f"occupancy from theta={min(theta_list)}° to theta={max(theta_list)}°")
        figname = f"{self.filename[:-5]}-angular acceptance.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


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
        plt.clf()


    def plot_angle_to_temperature(self):

        # load data
        self.load_metadicts()

        laser_t_list = []
        teta_list = []
        for data in self.meassurements:
            laser_t_list.append(data.metadict["Laser temp [°C]"])
            teta_list.append(data.metadict["theta [°]"])

        plt.figure()

        plt.scatter(np.array(teta_list), np.array(laser_t_list))

        plt.xlabel('theta [°]')
        plt.ylabel('Laser temperature')

        plt.title(f"Laser temperature from theta={min(teta_list)}° to theta={max(teta_list)}°")
        figname = f"{self.filename[:-5]}-angle_to_temp.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


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
        plt.clf()


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
        plt.clf()


    def plot_HV_to_occ(self):
        
        # load data
        self.load_metadicts()

        HV_list = []
        occ_list = []
        for data in self.meassurements:
            HV_list.append(data.metadict["Dy10 [V]"])
            occ_list.append(data.metadict["occ [%]"])

        plt.figure()

        plt.scatter(np.array(HV_list), np.array(occ_list))

        plt.xlabel('HV [V]')
        plt.ylabel('occ [%]')

        plt.title(f"occupancy from Dy10={min(HV_list)} V to Dy10={max(HV_list)} V")
        figname = f"{self.filename[:-5]}-HV_to_occ.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


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
        plt.clf()


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
        plt.clf()


    def plot_HV_to_PTV(self):

        # load data
        self.load_metadicts()

        ptv_list = []
        HV_list = []
        for data in self.meassurements:
            ptv_list.append(data.metadict["peak to valley ratio"])
            HV_list.append(data.metadict["Dy10 [V]"])

        plt.figure()

        plt.scatter(np.array(HV_list), np.array(ptv_list))

        plt.xlabel('Dy10 [V]')
        plt.ylabel('peak to valley ratio')

        plt.title(f"peak to valley ratio from Dy10={min(HV_list)} V to Dy10={max(HV_list)} V")
        figname = f"{self.filename[:-5]}-HV_to_PTV.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


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
        plt.clf()

    
    def plot_laser_tune_to_occ(self):
        
        # load data
        self.load_metadicts()

        laser_tune_list = []
        occ_list = []
        for data in self.meassurements:
            laser_tune_list.append(data.metadict["Laser tune [%]"])
            occ_list.append(data.metadict["occ [%]"])

        plt.figure()

        plt.scatter(np.array(laser_tune_list), np.array(occ_list))

        plt.xlabel('laser tune [%]')
        plt.ylabel('occ [%]')

        plt.title(f"occupancy from laser_tune={min(laser_tune_list)}% to laser_tune={max(laser_tune_list)}%")
        figname = f"{self.filename[:-5]}-laser_tune_to_occ.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_powermeter_to_PTV(self):

        # load data
        self.load_metadicts()

        ptv_list = []
        pw_list = []
        for data in self.meassurements:
            ptv_list.append(data.metadict["peak to valley ratio"])
            pw_list.append(data.metadict["Powermeter [pW]"])

        plt.figure()

        plt.scatter(np.array(pw_list), np.array(ptv_list))

        plt.xlabel('Powermeter value [pW]')
        plt.ylabel('peak to valley ratio')

        plt.title(f"powermeter to peak-to-valley ratio from {min(pw_list)} pW to {max(pw_list)} pW")
        figname = f"{self.filename[:-5]}-Powermeter_to_PTV.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()

    def plot_laser_tune_to_charge(self):
        
        # load data
        self.load_metadicts()

        laser_tune_list = []
        charge_list = []
        for data in self.meassurements:
            laser_tune_list.append(data.metadict["Laser tune [%]"])
            charge_list.append(data.metadict["charge [pC]"])

        plt.figure()

        plt.scatter(np.array(laser_tune_list), np.array(charge_list))

        plt.xlabel('laser tune [%]')
        plt.ylabel('charge [pC]')

        plt.title(f"charge from laser_tune={min(laser_tune_list)}% to laser_tune={max(laser_tune_list)}%")
        figname = f"{self.filename[:-5]}-laser_tune_to_charge.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()

    
    def plot_powermeter_to_charge(self):

        # load data
        self.load_metadicts()

        powermeter_list = []
        charge_list = []
        for data in self.meassurements:
            powermeter_list.append(data.metadict['Powermeter [pW]'])
            charge_list.append(data.metadict["charge [pC]"])

        x_data = np.array(powermeter_list)
        y_data = np.array(charge_list)
        
        plt.scatter(x_data, y_data, label='data points')
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
        plt.plot(x_data, intercept + slope*x_data, 'r', label='linear fit: y={:.2f}x+{:.2f}, $std$={:.2f}'.format(slope,intercept,std_err))
        plt.vlines(x_data, intercept + slope*x_data, y_data, linestyles='dotted', color='gray', linewidth=2)
        
        plt.xlabel('Laser output [pW]')
        plt.ylabel('charge at PMT anode [pC]')
        plt.legend()

        plt.title(f"PMT Charge Linearity")
        figname = f"{self.filename[:-5]}-powermeter_to_charge.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()


    def plot_HV_to_dark_count(self):
        
        #load data
        self.load_metadicts()

        HV_list = []
        DC_list = []
        for data in self.meassurements:
            HV_list.append(data.metadict["Dy10 [V]"])
            DC_list.append(data.metadict["dark rate [Hz]"])

        plt.figure()

        plt.scatter(np.array(HV_list), np.array(DC_list))

        plt.xlabel('Dy10 [V]')
        plt.ylabel('dark rate [Hz]')

        plt.title(f"dark rate from Dy10={min(HV_list)} to Dy10={max(HV_list)}")
        figname = f"{self.filename[:-5]}-HV_to_dark_count.png"

        save_dir = os.path.join(self.filepath, self.filename[:-5], "global-plots")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        plt.savefig(os.path.join(save_dir, figname))
        if config.ANALYSIS_SHOW_PLOTS:
            plt.show()
        plt.clf()

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

    def plot_average_wf(self):
        
        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)
                data.plot_average_wf()
                if clear: data.clear()
                

    def plot_hist(self, mode="amplitude", nr_bins=None, fitting_threshold=None):

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)

                data.plot_hist(mode, nr_bins, fitting_threshold)
                if clear: data.clear()


    def plot_transit_times(self, nr_bins = None):

        with h5py.File(os.path.join(self.filepath, self.filename), "r") as h5:

            for data in self.meassurements:

                clear = False
                if not data.waveforms:
                    clear = True
                    data.read_from_file(hdf5_connection=h5)

                data.plot_transit_times(nr_bins)
                if clear: data.clear()
