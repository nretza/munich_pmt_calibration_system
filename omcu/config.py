import numpy as np


#------------------------------------------------------

#setup

OUT_PATH  = "/home/canada/munich_pmt_calibration_system/data"
PMT_NAME  = None    #asks for name at runtime if None

LOG_FILE  = "omcu.log"	     # name of the log file
LOG_LVL   = 20		     # logging level (10: Debug, 20: Info, 30: Warning etc...)

COOLDOWN_TIME = 30          # Time in minutes before any measurements take place

#------------------------------------------------------

# which test protocols to choose

TUNE_PARAMETERS     = True  # not in use right now, will always tune
PHOTOCATHODE_SCAN   = True
FRONTAL_HV_SCAN     = True

#------------------------------------------------------

#Data-Analysis

ANALYSIS_PERFORM    = False    # perform data analysis after datataking
ANALYSIS_SHOW_PLOTS = False    # call plt.show()

#what to plot

ANALYSIS_PLOT_WFS       = False
ANALYSIS_PLOT_WF_AVG    = True
ANALYSIS_PLOT_WF_MSK    = False
ANALYSIS_PLOT_PEAKS     = False
ANALYSIS_PLOT_HIST_AMP  = False
ANALYSIS_PLOT_HIST_CHRG = False
ANALYSIS_PLOT_HIST_GAIN = True
ANALYSIS_PLOT_TTS       = True

#------------------------------------------------------

#tune

TUNE_MODE     = "iter"      # (none, iter, single, only_gain, only_occ)
TUNE_MAX_ITER = 10          # max iters for iter tune mode

#gain tune
TUNE_GAIN_MIN    = 4.9e6
TUNE_GAIN_MAX    = 5.1e6
TUNE_V_START     = None          # will start at current voltage when None
TUNE_V_STEP      = 5

#occ tune
TUNE_OCC_MIN        = 0.05
TUNE_OCC_MAX        = 0.10
TUNE_LASER_START    = None       # will start at current laser tune when None
TUNE_LASER_STEP     = 5

TUNE_NR_OF_WAVEFORMS  =  20000
TUNE_SIGNAL_THRESHOLD = -3

#-----------------------------------------------------

# photo-cathode scan
# A scan of different angles to determine e.g. angular acceptance

PCS_DATAFILE      = "data_photocathode_scan.hdf5"

PCS_PHI_LIST      = np.arange(0,90,10)           #phi angles to set while datataking (start,stop,step)
PCS_THETA_LIST    = np.arange(0,90,10)           #theta angles to set while datataking (start,stop,step)

PCS_NR_OF_WAVEFORMS     =  50000                 #Number of waveforms the picoscope should record per HV,phi,theta - configuration
PCS_SIGNAL_THRESHOLD    = -3                     #Determines when a waveform is considered a signal and will be written in the datafile
PCS_MEASUREMENT_SLEEP   =  1                     #Time in seconds that are waited before each recording of data

#------------------------------------------------------

# frontal HV scan
# A scan of different HVs at frontal facing light source

FHVS_DATAFILE      = "data_frontal_HV.hdf5"

FHVS_HV_LIST       = np.arange(950,1350,20)       #HVs to set while datataking (start,stop,step)

FHVS_NR_OF_WAVEFORMS     =  50000                 #Number of waveforms the picoscope should record per HV,phi,theta - configuration
FHVS_SIGNAL_THRESHOLD    = -3                     #Determines when a waveform is considered a signal and will be written in the datafile
FHVS_MEASUREMENT_SLEEP   =  1                     #Time in seconds that are waited before each recording of data
