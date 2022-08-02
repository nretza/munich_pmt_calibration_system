#!/usr/bin/python3

from data_analysis.data_handler import data_handler
import config
import os
#TODO: logging, printouts, other analysis, PCS

class Data_Analysis:

    def __init__(self, data_path):

        self.data_path = data_path

    def analyze_FHVS(self):
        file_name = os.path.join(self.data_path, config.FHVS_DATAFILE)
        handler = data_handler(file_name)
        handler.plot_wfs()
        handler.plot_peaks()
        handler.plot_average_wf()
        handler.plot_transit_times()
        for mode in ["amplitude", "gain", "charge"]:
            handler.plot_hist(mode)

    def analyze_PCS(self):
        file_name = os.path.join(self.data_path, config.PCS_DATAFILE)
        handler = data_handler(file_name)
        handler.plot_wfs()
        handler.plot_peaks()
        handler.plot_average_wf()
        handler.plot_transit_times()
        for mode in ["amplitude", "gain", "charge"]:
            handler.plot_hist(mode)
