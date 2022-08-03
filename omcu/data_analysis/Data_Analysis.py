#!/usr/bin/python3

from data_analysis.data_handler import data_handler
import config
import time

#TODO: logging

class Data_Analysis:

    def __init__(self, data_path):

        self.data_path = data_path

    def analyze_FHVS(self):

        print("\nPerforming Frontal HV Scan Analysis")
        start_time = time.time()
        handler = data_handler(config.FHVS_DATAFILE, self.data_path)

        if config.ANALYSIS_PLOT_WFS:
            print("Plotting waveform data")
            handler.plot_wfs()
        if config.ANALYSIS_PLOT_WF_MSK:
            print("Plotting waveform masks")
            handler.plot_wfs_mask()
        if config.ANALYSIS_PLOT_PEAKS:
            print("Plotting peaks")
            handler.plot_peaks()
        if config.ANALYSIS_PLOT_WF_AVG:
            print("Plotting average waveforms")
            handler.plot_average_wf()
        if config.ANALYSIS_PLOT_TTS:
            print("plotting transit time data")
            handler.plot_transit_times()
        if config.ANALYSIS_PLOT_HIST_AMP:
            print("plotting amlitude histograms")
            handler.plot_hist("amplitude")
        if config.ANALYSIS_PLOT_HIST_CHRG:
            print("plotting charge histograms")
            handler.plot_hist("charge")
        if config.ANALYSIS_PLOT_HIST_GAIN:
            print("plotting gain histograms")
            handler.plot_hist("gain")
            
        print(f"\nFinished frontal HV Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for FHVS Analysis: {round((end_time - start_time) / 60, 0)} minutes")


    def analyze_PCS(self):
        print("\nPerforming Photo Cathode Scan Analysis")
        start_time = time.time()
        handler = data_handler(config.PCS_DATAFILE, self.data_path)

        if config.ANALYSIS_PLOT_WFS:
            print("Plotting waveform data")
            handler.plot_wfs()
        if config.ANALYSIS_PLOT_WF_MSK:
            print("Plotting waveform masks")
            handler.plot_wfs_mask()
        if config.ANALYSIS_PLOT_PEAKS:
            print("Plotting peaks")
            handler.plot_peaks()
        if config.ANALYSIS_PLOT_WF_AVG:
            print("Plotting average waveforms")
            handler.plot_average_wf()
        if config.ANALYSIS_PLOT_TTS:
            print("plotting transit time data")
            handler.plot_transit_times()
        if config.ANALYSIS_PLOT_HIST_AMP:
            print("plotting amlitude histograms")
            handler.plot_hist("amplitude")
        if config.ANALYSIS_PLOT_HIST_CHRG:
            print("plotting charge histograms")
            handler.plot_hist("charge")
        if config.ANALYSIS_PLOT_HIST_GAIN:
            print("plotting gain histograms")
            handler.plot_hist("gain")

        print(f"\nFinished Photo Cathode Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for PCS Analysis: {round((end_time - start_time) / 60, 0)} minutes")
        