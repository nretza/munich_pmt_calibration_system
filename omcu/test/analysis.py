import os
import config
from data_analysis.data_handler import data_handler

data_path = ""


file_name = os.path.join(data_path, config.PCS_DATAFILE)
handler = data_handler(file_name)
handler.plot_wfs()
handler.plot_average_wf()

#todo weiter machen