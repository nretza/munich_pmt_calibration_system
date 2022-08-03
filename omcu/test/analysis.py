import os
import config_test
from data_analysis.data_handler import data_handler

data_path = "/mnt/c/Users/nikla/OneDrive/Dokumente/Studium/MSc_Physik/Master_Thesis/datasets/omcu_data/test"


file_name = os.path.join(data_path, config_test.PCS_DATAFILE)
handler = data_handler(file_name)
handler.plot_wfs()
handler.plot_average_wf()

#todo weiter machen