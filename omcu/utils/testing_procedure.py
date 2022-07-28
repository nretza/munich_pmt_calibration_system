#!/usr/bin/python3
import numpy
import time
import h5py
import os
import itertools

import config
from devices.Picoscope import Picoscope
from devices.PSU import PSU0, PSU1
from devices.Picoamp import Picoamp
from devices.Rotation import Rotation
from devices.Laser import Laser
from devices.Powermeter import Powermeter
from utils.util import *

#------------------------------------------------------------------------------

def tune_parameters(tune_mode="from_config"):

    start_time = time.time()

    if tune_mode == "from_config":
        tune_mode = config.TUNE_MODE

    if tune_mode == "single" or tune_mode == "only_occ":
        print(f"\ntuning occupancy between {config.TUNE_OCC_MIN} and {config.TUNE_OCC_MAX}")
        occ, laser_tune = tune_occ(occ_min=config.TUNE_OCC_MIN,
                                   occ_max=config.TUNE_OCC_MAX,
                                   laser_tune_start=config.TUNE_LASER_START,
                                   laser_tune_step=config.TUNE_LASER_STEP,
                                   threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                                   iterations=config.TUNE_NR_OF_WAVEFORMS)
        print(f"reached occupancy of {occ} at {laser_tune} laser tune value")

    if tune_mode == "single" or tune_mode == "only_gain":
        print(f"\ntuning gain between {config.TUNE_GAIN_MIN} and {config.TUNE_GAIN_MAX}")
        gain, HV = tune_gain(g_min=config.TUNE_GAIN_MIN,
                             g_max=config.TUNE_GAIN_MAX,
                             V_start=config.TUNE_V_START,
                             V_step=config.TUNE_V_STEP,
                             threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                             iterations=config.TUNE_NR_OF_WAVEFORMS)
        print(f"reached gain {gain} at Voltage of {HV} Volt")

    if tune_mode == "iter":
        iters = 0
        print(f"\ntuning occupancy between {config.TUNE_OCC_MIN} and {config.TUNE_OCC_MAX} and gain between {config.TUNE_GAIN_MIN} and {config.TUNE_GAIN_MAX} iteratively")
        while True:
            iters += 1
            _, laser_val = tune_occ(occ_min=config.TUNE_OCC_MIN,
                                    occ_max=config.TUNE_OCC_MAX,
                                    laser_tune_start=config.TUNE_LASER_START,
                                    laser_tune_step=config.TUNE_LASER_STEP,
                                    threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                                    iterations=config.TUNE_NR_OF_WAVEFORMS)
            _, HV_val = tune_gain(g_min=config.TUNE_GAIN_MIN,
                                  g_max=config.TUNE_GAIN_MAX,
                                  V_start=config.TUNE_V_START,
                                  V_step=config.TUNE_V_STEP,
                                  threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                                  iterations=config.TUNE_NR_OF_WAVEFORMS)
            #measure after tuning to avoid cross-influence
            occ = measure_occ(threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                              iterations=config.TUNE_NR_OF_WAVEFORMS)
            gain = measure_gain(threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                                iterations=config.TUNE_NR_OF_WAVEFORMS)
            if occ > config.TUNE_OCC_MIN and occ < config.TUNE_OCC_MAX and gain > config.TUNE_GAIN_MIN and gain:
                print(f"reached occupancy of {occ} at {laser_val} laser tune value and gain of {gain} at {HV_val} V.")
                break
            if iters >= config.TUNE_MAX_ITER:
                print(f"WARNING: could not reach desired tuning values within {config.TUNE_MAX_ITER} iterations. Aborting tuning!")
                print(f"reached occupancy of {occ} at {laser_val} laser tune value and gain of {gain} at {HV_val} V.")

    if tune_mode == "none":
        occ = measure_occ(threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                          iterations=config.TUNE_NR_OF_WAVEFORMS)
        gain = measure_gain(threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                            iterations=config.TUNE_NR_OF_WAVEFORMS)
        print(f"\nwill not tune gain and occupancy. measured:\nocc:\t{occ}\ngain:\t{gain}")

    if tune_mode not in ["none", "iter", "single", "only_gain", "only_occ"]:
        occ = measure_occ(threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                          iterations=config.TUNE_NR_OF_WAVEFORMS)
        gain = measure_gain(threshold_signal=config.TUNE_SIGNAL_THRESHOLD,
                            iterations=config.TUNE_NR_OF_WAVEFORMS)
        print(f"WARNING: Can not make sense of tuning mode. Will proceed without tuning. measured:\nocc:\t{occ}\ngain:\t{gain}")

    end_time = time.time()
    print(f"Total time for tuning: {round((end_time - start_time) / 60, 0)} minutes")


#------------------------------------------------------------------------------


def photocathode_scan(DATA_PATH):

    start_time = time.time()

    print(f"\nperforming photocathode scan over:\nPhi:\t{config.PCS_PHI_LIST}\nTheta:\t{config.PCS_THETA_LIST}")
    print(f"saving data in {os.path.join(DATA_PATH, config.PCS_DATAFILE)}")
    Rotation.Instance().go_home()

    with h5py.File(os.path.join(DATA_PATH, config.PCS_DATAFILE), 'w') as datafile:
        for phi, theta in itertools.product(config.PCS_PHI_LIST, config.PCS_THETA_LIST):  # loop through Theta, then phi
            print(f"\nmeasuring ---- Phi: {phi}\tTheta: {theta}")
            Rotation.Instance().set_position(phi, theta)

            time.sleep(config.PCS_MEASUREMENT_SLEEP)
            data_sgnl, data_trg = Picoscope.Instance().block_measurement(trgchannel=0,
                                                                         sgnlchannel=2,
                                                                         direction=2,
                                                                         threshold=2000,
                                                                         number=config.PCS_NR_OF_WAVEFORMS)
            data_filtr, trigger_filtr = filter_data_and_triggerset_by_threshold(threshold=config.PCS_SIGNAL_THRESHOLD,
                                                                                dataset=data_sgnl,
                                                                                triggerset=data_trg)

            time.sleep(config.PCS_MEASUREMENT_SLEEP)
            meta_dict = calc_meta_dict(data_sgnl, config.PCS_SIGNAL_THRESHOLD)

            nSamples = Picoscope.Instance().get_nSamples()
            arr_sgnl = datafile.create_dataset(f"theta{theta}/phi{phi}/signal", (len(data_filtr), nSamples, 2),
                                               'f')
            arr_trg = datafile.create_dataset(f"theta{theta}/phi{phi}/trigger",
                                              (len(trigger_filtr), nSamples, 2), 'f')

            arr_sgnl[:] = data_filtr
            arr_trg[:] = trigger_filtr

            for key in meta_dict:
                arr_sgnl.attrs[key] = meta_dict[key]
                arr_trg.attrs[key] = meta_dict[key]

    print(f"\nFinished photocadode scan\nData located at {os.path.join(DATA_PATH, config.PCS_DATAFILE)}")

    end_time = time.time()
    print(f"total time for photocathode scan: {round((end_time - start_time) / 60, 0)} minutes")

#------------------------------------------------------------------------------


def frontal_HV_scan(DATA_PATH):

    start_time = time.time()

    print(f"\nperforming frontal HV scan over:\nHV:\t{config.FHVS_HV_LIST}\n")
    print(f"saving data in {os.path.join(DATA_PATH, config.FHVS_DATAFILE)}")
    Rotation.Instance().go_home()

    with h5py.File(os.path.join(DATA_PATH, config.FHVS_DATAFILE), 'w') as datafile:
        for HV in config.FHVS_HV_LIST:  # loop through HV
            print(f"\nmeasuring ---- HV: {HV}")
            HV_supply.Instance().SetVoltage(HV)
            time.sleep(config.FHVS_MEASUREMENT_SLEEP)
            data_sgnl, data_trg = Picoscope.Instance().block_measurement(trgchannel=0,
                                                                         sgnlchannel=2,
                                                                         direction=2,
                                                                         threshold=2000,
                                                                         number=config.FHVS_NR_OF_WAVEFORMS)
            data_filtr, trigger_filtr = filter_data_and_triggerset_by_threshold(threshold=config.FHVS_SIGNAL_THRESHOLD,
                                                                                dataset=data_sgnl,
                                                                                triggerset=data_trg)
            time.sleep(config.FHVS_MEASUREMENT_SLEEP)
            meta_dict = calc_meta_dict(data_sgnl, config.FHVS_SIGNAL_THRESHOLD)

            nSamples = Picoscope.Instance().get_nSamples()
            arr_sgnl = datafile.create_dataset(f"HV{HV}/signal", (len(data_filtr), nSamples, 2),
                                               'f')
            arr_trg = datafile.create_dataset(f"HV{HV}/trigger",
                                              (len(trigger_filtr), nSamples, 2), 'f')

            arr_sgnl[:] = data_filtr
            arr_trg[:] = trigger_filtr

            for key in meta_dict:
                arr_sgnl.attrs[key] = meta_dict[key]
                arr_trg.attrs[key] = meta_dict[key]

    print(f"\nFinished frontal HV scan\nData located at {os.path.join(DATA_PATH, config.FHVS_DATAFILE)}")

    end_time = time.time()
    print(f"Total time for frontal HV scan: {round((end_time - start_time) / 60, 0)} minutes")