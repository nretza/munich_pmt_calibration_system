import os
import config_test
from data_analysis.data_handler import data_handler

data_path = "/home/canada/munich_pmt_calibration_system/data/R14374"

handler = data_handler(config_test.PCS_DATAFILE, data_path)

handler.plot_angluar_acceptance()

#TODO weiter machen