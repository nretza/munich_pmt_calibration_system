import numpy as np


#------------------------------------------------------

#setup

OUT_PATH  = "/home/canada/munich_pmt_calibration_system/data"
PMT_NAME  = None             #asks for name at runtime if None

LOG_FILE  = "omcu.log"	     # name of the log file
LOG_LVL   = 20		         # logging level (10: Debug, 20: Info, 30: Warning etc...)

COOLDOWN_TIME = 60           # Time in minutes before any measurements take place
COOLDOWN_HV   = 90

#------------------------------------------------------

# which test protocols to choose

TUNE_PARAMETERS     = True    # not in use right now, will always tune
PHOTOCATHODE_SCAN   = True
FRONTAL_HV_SCAN     = True

#------------------------------------------------------

#Data-Analysis

ANALYSIS_PERFORM    = True     # perform data analysis after datataking
ANALYSIS_SHOW_PLOTS = False    # call plt.show()

#what to plot

ANALYSIS_PLOT_WFS                = True
ANALYSIS_PLOT_WF_AVG             = True
ANALYSIS_PLOT_WF_MSK             = True
ANALYSIS_PLOT_PEAKS              = True
ANALYSIS_PLOT_HIST_AMP           = True
ANALYSIS_PLOT_HIST_CHRG          = True
ANALYSIS_PLOT_HIST_GAIN          = True
ANALYSIS_PLOT_TTS                = True
ANALYSIS_PLOT_ANGULAR_ACCEPTANCE = True

#------------------------------------------------------

#tune

TUNE_MODE     = "iter"      # (none, iter, single, only_gain, only_occ)
TUNE_MAX_ITER = 15          # max iters for iter tune mode

#gain tune
TUNE_GAIN_MIN    = 4.95e6
TUNE_GAIN_MAX    = 5.05e6
TUNE_V_START     = 90          # will start at current voltage when None
TUNE_V_STEP      = 1

#occ tune
TUNE_OCC_MIN        = 0.09
TUNE_OCC_MAX        = 0.10
TUNE_LASER_START    = None       # will start at current laser tune when None
TUNE_LASER_STEP     = 1

TUNE_NR_OF_WAVEFORMS  =  100000
TUNE_SIGNAL_THRESHOLD = -4

#-----------------------------------------------------

# photo-cathode scan
# A scan of different angles to determine e.g. angular acceptance

PCS_DATAFILE      = "data_photocathode_scan.hdf5"

PCS_PHI_LIST      = np.arange(0,  90, 5)          #phi angles to set while datataking (start,stop,step)
PCS_THETA_LIST    = np.arange(0, 105, 5)          #theta angles to set while datataking (start,stop,step)

PCS_NR_OF_WAVEFORMS     =  100000                 #Number of waveforms the picoscope should record per HV,phi,theta - configuration
PCS_SIGNAL_THRESHOLD    = -4                      #Determines when a waveform is considered a signal and will be written in the datafile
PCS_MEASUREMENT_SLEEP   =  1                      #Time in seconds that are waited before each recording of data

#------------------------------------------------------

# frontal HV scan
# A scan of different HVs at frontal facing light source

FHVS_DATAFILE      = "data_frontal_HV.hdf5"

FHVS_HV_LIST       = np.arange(70,110,2)       #HVs to set while datataking (start,stop,step)

FHVS_NR_OF_WAVEFORMS     =  100000                #Number of waveforms the picoscope should record per HV,phi,theta - configuration
FHVS_SIGNAL_THRESHOLD    = -4                     #Determines when a waveform is considered a signal and will be written in the datafile
FHVS_MEASUREMENT_SLEEP   =  1                     #Time in seconds that are waited before each recording of data
