#!/usr/bin/python3

if __name__ == "__main__":
    import sys
    sys.path.append("..")

import config
import time
import logging

from utils.DataHandler import DataHandler

class DataAnalysis:

    def __init__(self, data_path):

        self.data_path = data_path
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")


    def analyze_PCS(self):
        print("\nPerforming Photo Cathode Scan Analysis")
        start_time = time.time()
        handler = DataHandler(config.PCS_DATAFILE, self.data_path)

        if config.ANALYSIS_PLOT_WFS:
            print("Plotting waveform data")
            self.logger.info("Plotting waveform data")
            handler.plot_wfs()
        if config.ANALYSIS_PLOT_PEAKS:
            print("Plotting peaks")
            self.logger.info("Plotting peaks")
            handler.plot_peaks()
        if config.ANALYSIS_PLOT_WF_MSK:
            print("Plotting waveform masks")
            self.logger.info("Plotting waveform masks")
            handler.plot_wf_masks()
        if config.ANALYSIS_PLOT_WF_AVG:
            print("Plotting average waveforms")
            self.logger.info("Plotting average waveforms")
            handler.plot_average_wfs()
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
        if config.ANALYSIS_PLOT_TTS:
            print("plotting transit time data")
            self.logger.info("plotting transit time data")
            handler.plot_transit_times()

        if config.ANALYSIS_PLOT_ANGULAR_ACCEPTANCE:
            print("plotting angular acceptance")
            self.logger.info("plotting angular acceptance")
            handler.plot_angular_acceptance()
        if config.ANALYSIS_PLOT_ANGLE_TO_GAIN:
            print("plotting angle to gain relation")
            self.logger.info("plotting angle to gain relation")
            handler.plot_angle_to_gain()
        if config.ANALYSIS_PLOT_ANGLE_TO_TTS:
            print("plotting angle to TTS relation")
            self.logger.info("plotting angle to TTS relation")
            handler.plot_angle_to_TTS()
        if config.ANALYSIS_PLOT_ANGLE_TO_RISE_TIME:
            print("plotting angle to rise time relation")
            self.logger.info("plotting angle to rise time relation")
            handler.plot_angle_to_rise_time()

        print(f"\nFinished Photo Cathode Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for PCS Analysis: {round((end_time - start_time) / 60, 0)} minutes")
        


    def analyze_FHVS(self):

        print("\nPerforming Frontal HV Scan Analysis")
        self.logger.info("Performing Frontal HV Scan Analysis")
        start_time = time.time()
        handler = DataHandler(config.FHVS_DATAFILE, self.data_path)

        if config.ANALYSIS_PLOT_WFS:
            print("Plotting waveform data")
            self.logger.info("Plotting waveform data")
            handler.plot_wfs()
        if config.ANALYSIS_PLOT_PEAKS:
            print("Plotting peaks")
            self.logger.info("Plotting peaks")
            handler.plot_peaks()
        if config.ANALYSIS_PLOT_WF_MSK:
            print("Plotting waveform masks")
            self.logger.info("Plotting waveform masks")
            handler.plot_wf_masks()
        if config.ANALYSIS_PLOT_WF_AVG:
            print("Plotting average waveforms")
            self.logger.info("Plotting average waveforms")
            handler.plot_average_wfs()
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
        if config.ANALYSIS_PLOT_TTS:
            print("plotting transit time data")
            self.logger.info("plotting transit time data")
            handler.plot_transit_times()

        if config.ANALYSIS_PLOT_HV_TO_GAIN:
            print("plotting HV to gain relation")
            self.logger.info("plotting HV to gain relation")
            handler.plot_HV_to_gain()
        if config.ANALYSIS_PLOT_HV_TO_TTS:
            print("plotting HV to TTS relation")
            self.logger.info("plotting HV to TTS relation")
            handler.plot_HV_to_TTS()
        if config.ANALYSIS_PLOT_HV_TO_RISE_TIME:
            print("plotting HV to rise time relation")
            self.logger.info("plotting HV to rise time relation")
            handler.plot_HV_to_rise_time()            
            
        print(f"\nFinished frontal HV Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for FHVS Analysis: {round((end_time - start_time) / 60, 0)} minutes")


    def analyze_CLS(self):
        
        print("\nPerforming Charge Linearity Scan Analysis")
        self.logger.info("Performing Frontal HV Scan Analysis")
        start_time = time.time()
        handler = DataHandler(config.CLS_DATAFILE, self.data_path)

        if config.ANALYSIS_PLOT_WFS:
            print("Plotting waveform data")
            self.logger.info("Plotting waveform data")
            handler.plot_wfs()
        if config.ANALYSIS_PLOT_PEAKS:
            print("Plotting peaks")
            self.logger.info("Plotting peaks")
            handler.plot_peaks()
        if config.ANALYSIS_PLOT_WF_MSK:
            print("Plotting waveform masks")
            self.logger.info("Plotting waveform masks")
            handler.plot_wf_masks()
        if config.ANALYSIS_PLOT_WF_AVG:
            print("Plotting average waveforms")
            self.logger.info("Plotting average waveforms")
            handler.plot_average_wfs()
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
        if config.ANALYSIS_PLOT_TTS:
            print("plotting transit time data")
            self.logger.info("plotting transit time data")
            handler.plot_transit_times()

        # TODO

        print(f"\nFinished Charge Linearity Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for CLS Analysis: {round((end_time - start_time) / 60, 0)} minutes")



    def analyze_DCS(self):
        
        print("\nPerforming Dark Count Scan Analysis")
        self.logger.info("Performing Dark Count Scan Analysis")
        start_time = time.time()
       
       # TODO

        print(f"\nFinished Dark Count Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for DCS Analysis: {round((end_time - start_time) / 60, 0)} minutes")


if __name__ == "__main__":

    DATA_PATH = "/home/canada/munich_pmt_calibration_system/data/test/8/"

    print("analyzing data now")
    analysis = DataAnalysis(DATA_PATH)
    if config.FRONTAL_HV_SCAN:
        analysis.analyze_FHVS()
    if config.PHOTOCATHODE_SCAN:
        analysis.analyze_PCS()
    if config.CHARGE_LINEARITY_SCAN:
        analysis.analyze_CLS()
    if config.DARK_COUNT_SCAN:
        analysis.analyze_DCS()