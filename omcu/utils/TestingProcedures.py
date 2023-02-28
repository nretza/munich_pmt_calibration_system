#!/usr/bin/python3

import itertools
import logging
import os
import time

import config
import h5py
import numpy as np
from devices.Laser import Laser
from devices.Picoscope import Picoscope
from devices.Rotation import Rotation
from devices.uBase import uBase
from scipy.signal import find_peaks
from utils.util import tune_parameters

#------------------------------------------------------------------------------


def photocathode_scan(DATA_PATH):

    logging.getLogger("OMCU").info(f"entering PCS measurement")

    Laser.Instance().on_pulsed()
    Rotation.Instance().go_home()

    tune_parameters(tune_mode=config.PCS_TUNE_MODE,
                    nr_waveforms=config.PCS_TUNE_NR_OF_WAVEFORMS,
                    gain_min=config.PCS_TUNE_GAIN_MIN,
                    gain_max=config.PCS_TUNE_GAIN_MAX,
                    V_start=config.PCS_TUNE_V_START,
                    V_step=config.PCS_TUNE_V_STEP,
                    occ_min=config.PCS_TUNE_OCC_MIN,
                    occ_max=config.PCS_TUNE_OCC_MAX,
                    laser_start=config.PCS_TUNE_LASER_START,
                    laser_step=config.PCS_TUNE_LASER_STEP,
                    signal_threshold=config.PCS_TUNE_SIGNAL_THRESHOLD,
                    iterations=config.PCS_TUNE_MAX_ITER)

    start_time = time.time()

    print(f"\nperforming photocathode scan over:\nPhi:\t{config.PCS_PHI_LIST}\nTheta:\t{config.PCS_THETA_LIST}")
    print(f"saving data in {os.path.join(DATA_PATH, config.PCS_DATAFILE)}")


    with h5py.File(os.path.join(DATA_PATH, config.PCS_DATAFILE), 'w') as h5_connection:

        # loop through Theta, then phi
        for phi, theta in itertools.product(config.PCS_PHI_LIST, config.PCS_THETA_LIST):  

            print(f"\nmeasuring ---- Phi: {phi}\tTheta: {theta}")

            Rotation.Instance().set_position(phi, theta)

            time.sleep(config.PCS_MEASUREMENT_SLEEP)
            logging.getLogger("OMCU").info(f"measuring dataset of {config.PCS_NR_OF_WAVEFORMS} Waveforms from Picoscope")
            dataset = Picoscope.Instance().block_measurement(config.PCS_NR_OF_WAVEFORMS)

            if not dataset.calculate_occ(config.PCS_SIGNAL_THRESHOLD):
                logging.getLogger("OMCU").warning("Measured occupancy of 0. Will NOT store data and continue with next measurement.")
                print("Measured occupancy of 0. Will NOT store data and continue with next measurement.")
                continue

            logging.getLogger("OMCU").info(f"determining dataset metadata")
            dataset.meassure_metadict(signal_threshold=config.PCS_SIGNAL_THRESHOLD)
            logging.getLogger("OMCU").info(f"filtering dataset by threshold of {config.PCS_SIGNAL_THRESHOLD} mV")
            dataset.filter_by_threshold(signal_threshold=config.PCS_SIGNAL_THRESHOLD)
            logging.getLogger("OMCU").info(f"writing dataset to harddrive")
            dataset.setHDF5_key(f"theta {theta}/phi {phi}")
            dataset.write_to_file(hdf5_connection=h5_connection)

    print(f"\nFinished photocadode scan\nData located at {os.path.join(DATA_PATH, config.PCS_DATAFILE)}")

    Laser.Instance().off_pulsed()
    Rotation.Instance().go_home()

    end_time = time.time()
    print(f"total time for photocathode scan: {round((end_time - start_time) / 60, 0)} minutes")

    logging.getLogger("OMCU").info(f"PCS measurement complete")


#------------------------------------------------------------------------------


def frontal_HV_scan(DATA_PATH):

    logging.getLogger("OMCU").info(f"entering FHVS measurement")

    Laser.Instance().on_pulsed()
    Rotation.Instance().go_home()

    tune_parameters(tune_mode=config.FHVS_TUNE_MODE,
                    nr_waveforms=config.FHVS_TUNE_NR_OF_WAVEFORMS,
                    gain_min=config.FHVS_TUNE_GAIN_MIN,
                    gain_max=config.FHVS_TUNE_GAIN_MAX,
                    V_start=config.FHVS_TUNE_V_START,
                    V_step=config.FHVS_TUNE_V_STEP,
                    occ_min=config.FHVS_TUNE_OCC_MIN,
                    occ_max=config.FHVS_TUNE_OCC_MAX,
                    laser_start=config.FHVS_TUNE_LASER_START,
                    laser_step=config.FHVS_TUNE_LASER_STEP,
                    signal_threshold=config.FHVS_TUNE_SIGNAL_THRESHOLD,
                    iterations=config.FHVS_TUNE_MAX_ITER)

    start_time = time.time()

    print(f"\nperforming frontal HV scan over:\nHV:\t{config.FHVS_HV_LIST}\n")
    print(f"saving data in {os.path.join(DATA_PATH, config.FHVS_DATAFILE)}")
    Rotation.Instance().go_home()

    with h5py.File(os.path.join(DATA_PATH, config.FHVS_DATAFILE), 'w') as h5_connection:

        # loop through HV
        for HV in config.FHVS_HV_LIST: 

            print(f"\nmeasuring ---- HV: {HV}")

            uBase.Instance().SetVoltage(HV)

            time.sleep(config.FHVS_MEASUREMENT_SLEEP)
            logging.getLogger("OMCU").info(f"measuring dataset of {config.FHVS_NR_OF_WAVEFORMS} Waveforms from Picoscope")
            dataset = Picoscope.Instance().block_measurement(config.FHVS_NR_OF_WAVEFORMS)

            if not dataset.calculate_occ(config.FHVS_SIGNAL_THRESHOLD):
                logging.getLogger("OMCU").warning("Measured occupancy of 0. Will NOT store data and continue with next measurement.")
                print("Measured occupancy of 0. Will NOT store data and continue with next measurement.")
                continue

            logging.getLogger("OMCU").info(f"determining dataset metadata")
            dataset.meassure_metadict(signal_threshold=config.FHVS_SIGNAL_THRESHOLD)
            logging.getLogger("OMCU").info(f"filtering dataset by threshold of {config.FHVS_SIGNAL_THRESHOLD} mV")
            dataset.filter_by_threshold(signal_threshold=config.FHVS_SIGNAL_THRESHOLD)
            logging.getLogger("OMCU").info(f"writing dataset to harddrive")
            dataset.setHDF5_key(f"HV {HV}")
            dataset.write_to_file(hdf5_connection=h5_connection)

    print(f"\nFinished frontal HV scan\nData located at {os.path.join(DATA_PATH, config.FHVS_DATAFILE)}")

    Laser.Instance().off_pulsed()
    Rotation.Instance().go_home()

    end_time = time.time()
    print(f"Total time for frontal HV scan: {round((end_time - start_time) / 60, 0)} minutes")

    logging.getLogger("OMCU").info(f"FHVS measurement complete")
    

#------------------------------------------------------------------------------


def charge_linearity_scan(DATA_PATH):

    logging.getLogger("OMCU").info(f"entering CLS measurement")

    Laser.Instance().on_pulsed()
    Rotation.Instance().go_home()

    tune_parameters(tune_mode=config.CLS_TUNE_MODE,
                    nr_waveforms=config.CLS_TUNE_NR_OF_WAVEFORMS,
                    gain_min=config.CLS_TUNE_GAIN_MIN,
                    gain_max=config.CLS_TUNE_GAIN_MAX,
                    V_start=config.CLS_TUNE_V_START,
                    V_step=config.CLS_TUNE_V_STEP,
                    occ_min=config.CLS_TUNE_OCC_MIN,
                    occ_max=config.CLS_TUNE_OCC_MAX,
                    laser_start=config.CLS_TUNE_LASER_START,
                    laser_step=config.CLS_TUNE_LASER_STEP,
                    signal_threshold=config.CLS_TUNE_SIGNAL_THRESHOLD,
                    iterations=config.CLS_TUNE_MAX_ITER)

    start_time = time.time()

    print(f"\nperforming charge linearity scan over:\nlaser tune:\t{config.CLS_LASER_TUNE_LIST}\n")
    print(f"saving data in {os.path.join(DATA_PATH, config.CLS_DATAFILE)}")
    Rotation.Instance().go_home()

    with h5py.File(os.path.join(DATA_PATH, config.CLS_DATAFILE), 'w') as h5_connection:

        # loop through laser tune
        for laser_tune in config.CLS_LASER_TUNE_LIST: 

            print(f"\nmeasuring ---- laser tune: {laser_tune}")

            Laser.Instance().set_tune_value(laser_tune)

            time.sleep(config.CLS_MEASUREMENT_SLEEP)
            logging.getLogger("OMCU").info(f"measuring dataset of {config.CLS_NR_OF_WAVEFORMS} Waveforms from Picoscope")
            dataset = Picoscope.Instance().block_measurement(config.CLS_NR_OF_WAVEFORMS)

            if not dataset.calculate_occ(config.CLS_SIGNAL_THRESHOLD):
                logging.getLogger("OMCU").warning("Measured occupancy of 0. Will NOT store data and continue with next measurement.")
                print("Measured occupancy of 0. Will NOT store data and continue with next measurement.")
                continue

            logging.getLogger("OMCU").info(f"determining dataset metadata")
            dataset.meassure_metadict(signal_threshold=config.CLS_SIGNAL_THRESHOLD)
            logging.getLogger("OMCU").info(f"filtering dataset by threshold of {config.CLS_SIGNAL_THRESHOLD} mV")
            dataset.filter_by_threshold(signal_threshold=config.CLS_SIGNAL_THRESHOLD)
            logging.getLogger("OMCU").info(f"writing dataset to harddrive")
            dataset.setHDF5_key(f"laser tune {laser_tune}")
            dataset.write_to_file(hdf5_connection=h5_connection)

    print(f"\nFinished charge linearity scan\nData located at {os.path.join(DATA_PATH, config.CLS_DATAFILE)}")

    Laser.Instance().off_pulsed()
    Rotation.Instance().go_home()

    end_time = time.time()
    print(f"Total time for charge linearity scan: {round((end_time - start_time) / 60, 0)} minutes")

    logging.getLogger("OMCU").info(f"CLS measurement complete")



#------------------------------------------------------------------------------


def dark_count_scan(DATA_PATH):

    logging.getLogger("OMCU").info(f"entering DCS measurement")

    Laser.Instance().off_pulsed()
    Rotation.Instance().go_home()

    start_time = time.time()

    print(f"\nperforming dark count scan over:\nHV:\t{config.DCS_HV_LIST}\n")
    print(f"saving data in {os.path.join(DATA_PATH, config.DCS_DATAFILE)}")

    with h5py.File(os.path.join(DATA_PATH, config.DCS_DATAFILE), 'w') as h5_connection:

        # loop through HV
        for HV in config.DCS_HV_LIST: 

            print(f"\nmeasuring ---- HV: {HV}")

            uBase.Instance().SetVoltage(HV)

            time.sleep(config.DCS_MEASUREMENT_SLEEP)
            for i in range(config.DCS_NR_OF_ITERATIONS):
                logging.getLogger("OMCU").info(f"measuring dataset of {config.DCS_NR_OF_WAVEFORMS} Waveforms with {config.DCS_NR_OF_SAMPLES} samples from Picoscope")
                dataset = Picoscope.Instance().get_datastream(config.DCS_NR_OF_SAMPLES, config.DCS_NR_OF_WAVEFORMS)
                arr_sgnl             = h5_connection.create_dataset(f"HV {HV}/data-{i}", (config.DCS_NR_OF_WAVEFORMS, config.DCS_NR_OF_SAMPLES, 2),'f')
                arr_sgnl[:]          = dataset.astype(np.float16) # downsampling to avoid high data load

                arr_sgnl.attrs["HV"]             = uBase.Instance().getDy10()
                arr_sgnl.attrs["sgnl_threshold"] = config.DCS_SIGNAL_THRESHOLD
                arr_sgnl.attrs["peaks"]          = len(find_peaks(-dataset[:,:,1].flatten(), height=-config.DCS_SIGNAL_THRESHOLD, width=2)[0])

    print(f"\nFinished charge linearity scan\nData located at {os.path.join(DATA_PATH, config.DCS_DATAFILE)}")

    Laser.Instance().off_pulsed()
    Rotation.Instance().go_home()

    end_time = time.time()
    print(f"Total time for Dark Count Scan: {round((end_time - start_time) / 60, 0)} minutes")

    logging.getLogger("OMCU").info(f"DCS measurement complete")