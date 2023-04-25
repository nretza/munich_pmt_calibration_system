#!/usr/bin/python3

if __name__ == "__main__":
    import sys
    sys.path.append("/home/canada/munich_pmt_calibration_system/omcu")

import logging
import time

import config
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
            handler.plot_average_wf()
        if config.ANALYSIS_PLOT_HIST_AMP:
            print("Plotting amlitude histograms")
            self.logger.info("Plotting amlitude histograms")
            handler.plot_hist("amplitude")
        if config.ANALYSIS_PLOT_HIST_CHRG:
            print("Plotting charge histograms")
            self.logger.info("Plotting charge histograms")
            handler.plot_hist("charge")
        if config.ANALYSIS_PLOT_HIST_GAIN:
            print("Plotting gain histograms")
            self.logger.info("Plotting gain histograms")
            handler.plot_hist("gain")
        if config.ANALYSIS_PLOT_TTS:
            print("Plotting transit time data")
            self.logger.info("Plotting transit time data")
            handler.plot_transit_times()

        if config.ANALYSIS_PLOT_ANGULAR_ACCEPTANCE:
            print("Plotting angular acceptance")
            self.logger.info("Plotting angular acceptance")
            handler.plot_angular_acceptance()
        if config.ANALYSIS_PLOT_ANGLE_TO_GAIN:
            print("Plotting angle to gain relation")
            self.logger.info("Plotting angle to gain relation")
            handler.plot_angle_to_gain()
        if config.ANALYSIS_PLOT_ANGLE_TO_TTS:
            print("Plotting angle to TTS relation")
            self.logger.info("Plotting angle to TTS relation")
            handler.plot_angle_to_TTS()
        if config.ANALYSIS_PLOT_ANGLE_TO_RISE_TIME:
            print("Plotting angle to rise time relation")
            self.logger.info("Plotting angle to rise time relation")
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
            handler.plot_average_wf()
        if config.ANALYSIS_PLOT_HIST_AMP:
            print("Plotting amlitude histograms")
            self.logger.info("Plotting amlitude histograms")
            handler.plot_hist("amplitude")
        if config.ANALYSIS_PLOT_HIST_CHRG:
            print("Plotting charge histograms")
            self.logger.info("Plotting charge histograms")
            handler.plot_hist("charge")
        if config.ANALYSIS_PLOT_HIST_GAIN:
            print("Plotting gain histograms")
            self.logger.info("Plotting gain histograms")
            handler.plot_hist("gain")
        if config.ANALYSIS_PLOT_TTS:
            print("Plotting transit time data")
            self.logger.info("Plotting transit time data")
            handler.plot_transit_times()

        if config.ANALYSIS_PLOT_HV_TO_OCC:
            print("Plotting HV to occ relation")
            self.logger.info("Plotting HV to occ relation")
            handler.plot_HV_to_occ()           
        if config.ANALYSIS_PLOT_HV_TO_GAIN:
            print("Plotting HV to gain relation")
            self.logger.info("Plotting HV to gain relation")
            handler.plot_HV_to_gain()
        if config.ANALYSIS_PLOT_HV_TO_TTS:
            print("Plotting HV to TTS relation")
            self.logger.info("Plotting HV to TTS relation")
            handler.plot_HV_to_TTS()
        if config.ANALYSIS_PLOT_HV_TO_RISE_TIME:
            print("Plotting HV to rise time relation")
            self.logger.info("Plotting HV to rise time relation")
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
            handler.plot_average_wf()
        if config.ANALYSIS_PLOT_HIST_AMP:
            print("Plotting amlitude histograms")
            self.logger.info("Plotting amlitude histograms")
            handler.plot_hist("amplitude")
        if config.ANALYSIS_PLOT_HIST_CHRG:
            print("Plotting charge histograms")
            self.logger.info("Plotting charge histograms")
            handler.plot_hist("charge")
        if config.ANALYSIS_PLOT_HIST_GAIN:
            print("Plotting gain histograms")
            self.logger.info("Plotting gain histograms")
            handler.plot_hist("gain")
        if config.ANALYSIS_PLOT_TTS:
            print("Plotting transit time data")
            self.logger.info("Plotting transit time data")
            handler.plot_transit_times()

        if config.ANALYSIS_PLOT_LASER_TUNE_TO_OCC:
            print("Plotting laser tune to occ relation")
            self.logger.info("Plotting laser tune to occ relation")
            handler.plot_laser_tune_to_occ()
        if config.ANALYSIS_PLOT_LASER_TUNE_TO_CHARGE:
            print("Plotting laser tune to charge relation")
            self.logger.info("Plotting laser tune to gain relation")
            handler.plot_laser_tune_to_charge()

        print(f"\nFinished Charge Linearity Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for CLS Analysis: {round((end_time - start_time) / 60, 0)} minutes")


    def analyze_DCS(self):
        
        print("\nPerforming Dark Count Scan Analysis")
        self.logger.info("Performing Dark Count Scan Analysis")
        start_time = time.time()
        handler = DataHandler(config.DCS_DATAFILE, self.data_path)
       
        if config.ANALYSIS_PLOT_HV_TO_DARK_COUNT:
            print("Plotting HV to dark count relation")
            self.logger.info("Plotting HV to dark count relation")
            handler.plot_HV_to_dark_count()

        print(f"\nFinished Dark Count Scan Analysis\nData located in {self.data_path}")
        end_time = time.time()
        print(f"Total time for DCS Analysis: {round((end_time - start_time) / 60, 0)} minutes")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        DATA_PATH = sys.argv[1]
    else:
        DATA_PATH = "/home/canada/munich_pmt_calibration_system/data/marias_PMTs/122_no_gelpad"

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