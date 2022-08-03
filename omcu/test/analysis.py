import os
import config_test
from data_analysis.data_handler import data_handler

data_path = "/home/canada/munich_pmt_calibration_system/data/test"

handler = data_handler(config_test.FHVS_DATAFILE, data_path)
#handler.plot_wfs()
#handler.plot_wfs_mask()
#handler.plot_average_wf()
#handler.plot_peaks()
handler.plot_hist("amplitude")
handler.plot_hist("charge")
handler.plot_hist("gain")
handler.plot_transit_times()

#TODO weiter machen