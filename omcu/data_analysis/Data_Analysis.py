#!/usr/bin/python3

from data_analysis.data_handler import data_handler
import config
import time

#TODO: logging, printouts, other analysis, PCS

class Data_Analysis:

    def __init__(self, data_path):

        self.data_path = data_path

    def analyze_FHVS(self):
        print("\nPerforming Frontal HV Scan Analysis")
        start_time = time.time()
        handler = data_handler(config.FHVS_DATAFILE, self.data_path)
        print("Plotting waveform data")
        handler.plot_wfs()
        handler.plot_peaks()
        handler.plot_average_wf()
        print("plotting transit time data")
        handler.plot_transit_times()
        print("plotting histograms")
        for mode in ["amplitude", "gain", "charge"]:
            handler.plot_hist(mode)

        print(f"\nFinished frontal HV Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for FHVS Analysis: {round((end_time - start_time) / 60, 0)} minutes")


    def analyze_PCS(self):
        print("\nPerforming Photo Cathode Scan Analysis")
        start_time = time.time()
        handler = data_handler(config.PCS_DATAFILE, self.data_path)
        print("Plotting waveform data")
        handler.plot_wfs()
        handler.plot_peaks()
        handler.plot_average_wf()
        print("plotting transit time data")
        handler.plot_transit_times()
        print("plotting histograms")
        for mode in ["amplitude", "gain", "charge"]:
            handler.plot_hist(mode)
        print(f"\nFinished Photo Cathode Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for PCS Analysis: {round((end_time - start_time) / 60, 0)} minutes")
        