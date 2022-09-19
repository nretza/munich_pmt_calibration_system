#!/usr/bin/python3

if __name__ == "__main__":
    import sys
    sys.path.append("..")

from data_analysis.data_handler import data_handler
import config
import time
import logging

#TODO: logging

class Data_Analysis:

    def __init__(self, data_path):

        self.data_path = data_path
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")

    def analyze_FHVS(self):

        print("\nPerforming Frontal HV Scan Analysis")
        self.logger.info("Performing Frontal HV Scan Analysis")
        start_time = time.time()
        handler = data_handler(config.FHVS_DATAFILE, self.data_path)

        if config.ANALYSIS_PLOT_WFS:
            print("Plotting waveform data")
            self.logger.info("Plotting waveform data")
            handler.plot_wfs()
        if config.ANALYSIS_PLOT_WF_MSK:
            print("Plotting waveform masks")
            self.logger.info("Plotting waveform masks")
            handler.plot_wfs_mask()
        if config.ANALYSIS_PLOT_PEAKS:
            print("Plotting peaks")
            self.logger.info("Plotting peaks")
            handler.plot_peaks()
        if config.ANALYSIS_PLOT_WF_AVG:
            print("Plotting average waveforms")
            self.logger.info("Plotting average waveforms")
            handler.plot_average_wf()
        if config.ANALYSIS_PLOT_TTS:
            print("plotting transit time data")
            self.logger.info("plotting transit time data")
            handler.plot_transit_times()
        if config.ANALYSIS_PLOT_HIST_AMP:
            print("plotting amlitude histograms")
            self.logger.info("plotting amlitude histograms")
            handler.plot_hist("amplitude")
        if config.ANALYSIS_PLOT_HIST_CHRG:
            print("plotting charge histograms")
            self.logger.info("plotting charge histograms")
            handler.plot_hist("charge")
        if config.ANALYSIS_PLOT_HIST_GAIN:
            print("plotting gain histograms")
            self.logger.info("plotting gain histograms")
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
            self.logger.info("Plotting waveform data")
            handler.plot_wfs()
        if config.ANALYSIS_PLOT_WF_MSK:
            print("Plotting waveform masks")
            self.logger.info("Plotting waveform masks")
            handler.plot_wfs_mask()
        if config.ANALYSIS_PLOT_PEAKS:
            print("Plotting peaks")
            self.logger.info("Plotting peaks")
            handler.plot_peaks()
        if config.ANALYSIS_PLOT_WF_AVG:
            print("Plotting average waveforms")
            self.logger.info("Plotting average waveforms")
            handler.plot_average_wf()
        if config.ANALYSIS_PLOT_TTS:
            print("plotting transit time data")
            self.logger.info("plotting transit time data")
            handler.plot_transit_times()
        if config.ANALYSIS_PLOT_HIST_AMP:
            print("plotting amlitude histograms")
            self.logger.info("plotting amlitude histograms")
            handler.plot_hist("amplitude")
        if config.ANALYSIS_PLOT_HIST_CHRG:
            print("plotting charge histograms")
            self.logger.info("plotting charge histograms")
            handler.plot_hist("charge")
        if config.ANALYSIS_PLOT_HIST_GAIN:
            print("plotting gain histograms")
            self.logger.info("plotting gain histograms")
            handler.plot_hist("gain")
        if config.ANALYSIS_PLOT_ANGULAR_ACCEPTANCE:
            print("plotting angular acceptance")
            self.logger.info("plotting angular acceptance")
            handler.plot_angluar_acceptance()

        print(f"\nFinished Photo Cathode Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for PCS Analysis: {round((end_time - start_time) / 60, 0)} minutes")
        

if __name__ == "__main__":

    DATA_PATH = "/home/canada/munich_pmt_calibration_system/data/R14374/morning_after"

    print("analyzing data now")
    analysis = Data_Analysis(DATA_PATH)
    if config.FRONTAL_HV_SCAN:
        analysis.analyze_FHVS()
    if config.PHOTOCATHODE_SCAN:
         analysis.analyze_PCS()