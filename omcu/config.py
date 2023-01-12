#!/usr/bin/python3

import numpy as np

#------------------------------------------------------
#--------------   GENERAL          --------------------
#------------------------------------------------------

#setup

OUT_PATH  = "/home/canada/munich_pmt_calibration_system/data"
PMT_NAME  = None             #asks for name at runtime if None

LOG_FILE  = "omcu.log"	     # name of the log file
LOG_LVL   = 10		         # logging level (10: Debug, 20: Info, 30: Warning etc...)

COOLDOWN_TIME = 0           # Time in minutes before any measurements take place
COOLDOWN_HV   = 90

#------------------------------------------------------

# which test protocols to choose

PHOTOCATHODE_SCAN   = True
FRONTAL_HV_SCAN     = False

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
#--------------   PHOTOCATHODE SCAN   -----------------
#------------------------------------------------------

# an angular scan under constant gain / HV

PCS_DATAFILE      = "data_photocathode_scan.hdf5"

#-----------------------------------------------------

#tune

PCS_TUNE_MODE     = "none"      # (none, iter, single, only_gain, only_occ)
PCS_TUNE_MAX_ITER = 15          # max iters for iter tune mode

#gain tune
PCS_TUNE_GAIN_MIN    = 4.95e6
PCS_TUNE_GAIN_MAX    = 5.05e6
PCS_TUNE_V_START     = 90          # will start at current voltage when None
PCS_TUNE_V_STEP      = 1

#occ tune
PCS_TUNE_OCC_MIN        = 0.09
PCS_TUNE_OCC_MAX        = 0.10
PCS_TUNE_LASER_START    = None       # will start at current laser tune when None
PCS_TUNE_LASER_STEP     = 1

PCS_TUNE_NR_OF_WAVEFORMS  =  100000
PCS_TUNE_SIGNAL_THRESHOLD = -4

#-----------------------------------------------------

PCS_PHI_LIST      = np.arange(0,  90, 60)          #phi angles to set while datataking (start,stop,step)
PCS_THETA_LIST    = np.arange(0, 105, 60)          #theta angles to set while datataking (start,stop,step)

PCS_NR_OF_WAVEFORMS     =  100000                 #Number of waveforms the picoscope should record per HV,phi,theta - configuration
PCS_SIGNAL_THRESHOLD    = -4                      #Determines when a waveform is considered a signal and will be written in the datafile
PCS_MEASUREMENT_SLEEP   =  1                      #Time in seconds that are waited before each recording of data




#------------------------------------------------------
#--------------   FRONTAL HV SCAN     -----------------
#------------------------------------------------------

# a scan of different HVs at frontal facing light source

FHVS_DATAFILE      = "data_frontal_HV.hdf5"

#------------------------------------------------------

#tune

FHVS_TUNE_MODE     = "only_occ"      # (none, iter, single, only_gain, only_occ)
FHVS_TUNE_MAX_ITER = 15              # max iters for iter tune mode

#gain tune
FHVS_TUNE_GAIN_MIN    = None
FHVS_TUNE_GAIN_MAX    = None
FHVS_TUNE_V_START     = None          # will start at current voltage when None
FHVS_TUNE_V_STEP      = None

#occ tune
FHVS_TUNE_OCC_MIN        = 0.09
FHVS_TUNE_OCC_MAX        = 0.10
FHVS_TUNE_LASER_START    = None       # will start at current laser tune when None
FHVS_TUNE_LASER_STEP     = 1

FHVS_TUNE_NR_OF_WAVEFORMS  =  100000
FHVS_TUNE_SIGNAL_THRESHOLD = -4

#------------------------------------------------------

FHVS_HV_LIST       = np.arange(70,110,1)       #HVs to set while datataking (start,stop,step)

FHVS_NR_OF_WAVEFORMS     =  100000                #Number of waveforms the picoscope should record per HV,phi,theta - configuration
FHVS_SIGNAL_THRESHOLD    = -4                     #Determines when a waveform is considered a signal and will be written in the datafile
FHVS_MEASUREMENT_SLEEP   =  1                     #Time in seconds that are waited before each recording of data
