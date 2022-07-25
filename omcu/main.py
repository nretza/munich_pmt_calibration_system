import os
import argparse
import itertools
import h5py

from devices.Picoscope import Picoscope
from devices.PSU import PSU0, PSU1
from devices.Picoamp import Picoamp
from devices.Rotation import Rotation
from devices.Laser import Laser
from devices.Powermeter import Powermeter
from devices.device import device, serial_device
from util import *
import config


OUT_PATH    = config.OUT_PATH
PMT_NAME    = config.PMT_NAME
LOG_FILE    = config.LOG_FILE
LOG_LVL     = config.LOG_LVL
DATA_FILE   = config.DATA_FILE

COOLDOWN_TIME = config.COOLDOWN_TIME

HV_LIST       = config.HV_LIST
PHI_LIST      = config.PHI_LIST
THETA_LIST    = config.THETA_LIST

def main():

    # setup dirs and logging
    if not os.path.exists(OUT_PATH):
        raise FileNotFoundError(f"ERROR: given path {OUT_PATH} does not exist!")
    if not PMT_NAME:
        pmt_name = input("\nPlease enter the Name of the PMT inside the OMCU:\t") #TODO: apply filter for illegal chars here
    else:
        pmt_name = PMT_NAME
    DATA_PATH = os.path.join(OUT_PATH, pmt_name)
    while os.path.exists(DATA_PATH):
        pmt_name = input("ERROR: given PMT name seems to have Data stored already! Please choose another name:\t")
        DATA_PATH = os.path.join(OUT_PATH, pmt_name)
    os.mkdir(DATA_PATH)
    setup_file_logging(logging_file=os.path.join(DATA_PATH,LOG_FILE), logging_level=LOG_LVL)
    logging.getLogger("OMCU").info(f"storing data in {DATA_PATH}")

    # user input to confirm device setup    
    print("\nPlease make sure that the following conditions are met before the OMCU is turned on:\n")
    print("1.)\tThe PMT is connected to the HV supply via the coaxial cable labeled \"HV\" inside the OMCU.")
    print("2.)\tThe PMT is connected to the Picoscope via the coaxial cable labeled \"Data\" inside the OMCU.")
    print("3.)\tThe OMCU is properly closed and the red handles are shut.")
    print("4.)\tThe following devices to the left of the OMCU are turned on:")
    print("\t\t - the Power Meter")
    print("\t\t - the Laser Control System")
    print("\t\t - both PSU_0 and PSU_1")
    print("\t\t - the Picoscope")
    print("\t\t - the Picoamp")
    print("\t\t - the HV Supply - Please call your electronics expert to switch this device on!\n")
    check = input("Please confirm that the OMCU is properly set up [Yes/no]:\t")
    if not (check.lower() == "yes" or check.lower() == "y"):
        print("ERROR: OMCU determined as not set up by user input. Exiting program. Good bye!")
        exit()


    #Turn relevant devices on
    try:
        PSU1.Instance().on()
    except:
        print(f"\nERROR:\t PSU_1 could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(101)
    try:
        Rotation.Instance().go_home()
    except:
        print(f"\nERROR:\t Rotation Stage could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(102)
    try:
        Laser.Instance().on_pulsed()
    except:
        print(f"\nERROR:\t Laser could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(103)
    try:
        HV_supply.Instance().on()
    except:
        print(f"\nERROR:\t HV_supply could not be connected to successfully.\n \
        Please make sure the device is turned on by the hands of an electronic expert and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(104)
    try:
        Powermeter.Instance()
    except:
        print(f"\nERROR:\t Powermeter could not be connected to successfully.\n \
        Please make sure the device is turned on by the hands of an electronic expert and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(105)

    #time to reduce noise
    print(f"\nOMCU turned on successfully. Entering cooldown time of {COOLDOWN_TIME} minutes before taking measurements")
    for i in range(COOLDOWN_TIME):
        remain = COOLDOWN_TIME - i
        print(f"{remain} minutes of cooldown remaining")
        time.sleep(60)
    print("cooldown completed!")

    #tune parameters (seperate function because its pretty long)
    tune_parameters()

    # datataking
    print(f"\nperforming full photocadode scan over:\nHV:\t{HV_LIST}\nPhi:\t{PHI_LIST}\nTheta:\t{THETA_LIST}")
    print(f"saving data in {os.path.join(DATA_PATH, DATA_FILE)}")
    with h5py.File(os.path.join(DATA_PATH, DATA_FILE), 'w') as datafile:
        for phi, theta, HV in itertools.product(PHI_LIST, THETA_LIST, HV_LIST): #loop through HV, then Theta, then phi
            print(f"\nmeasuring ---- HV:{HV}\tPhi: {phi}\tTheta: {theta}")
            Rotation.Instance().set_position(phi, theta)
            HV_supply.Instance().SetVoltage(HV)
            time.sleep(config.MEASUREMENT_SLEEP)
            meta_dict = calc_meta_dict()
            time.sleep(config.MEASUREMENT_SLEEP)
            data_sgnl, data_trg = Picoscope.Instance().block_measurement(trgchannel=0,
                                                       sgnlchannel=2,
                                                       direction=2,
                                                       threshold=2000,
                                                       number=config.NR_OF_WAVEFORMS)
            data_filtr, trigger_filtr = filter_data_and_triggerset_by_threshold(threshold=config.SIGNAL_THRESHOLD,
                                                                                dataset=data_sgnl,
                                                                                triggerset=data_trg)
            nSamples = Picoscope.Instance().get_nSamples()
            arr_sgnl = datafile.create_dataset(f"theta{theta}/phi{phi}/HV{HV}/signal", (len(data_filtr), nSamples, 2), 'f')
            arr_trg  = datafile.create_dataset(f"theta{theta}/phi{phi}/HV{HV}/trigger", (len(trigger_filtr), nSamples, 2), 'f')

            arr_sgnl[:] = data_filtr
            arr_trg[:]  = trigger_filtr

            for key in meta_dict:
                arr_sgnl.attrs[key] = meta_dict[key]
                arr_trg.attrs[key] = meta_dict[key]

        print(f"finished photocadode scan, data located at {os.path.join(DATA_PATH, DATA_FILE)}")
    
    #turn devices off
    HV_supply.Instance().off_all()
    Laser.Instance().off_pulsed()
    PSU1.Instance().off()

    print("\nend of program reached, nothing to execute anymore.\nPLEASE MAKE SURE TO TURN ALL DEVICES OFF BEFORE OPENING THE OMCU\nGood bye!")
    exit(0)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(   description='Control Software fpr the Optical Module Calibration Unit.',
                                        add_help=True,
                                        epilog="for further help, please contact author: niklas.retza@tum.de")

    parser.add_argument('-o', '--outpath',  help='path to the program output',  action="store")
    parser.add_argument('-l', '--loglvl', help='the logging level for the log output file', action="store")
    parser.add_argument('-n', '--pmtname',  help='name of the PMT inside the omcu',  action="store")
    parser.add_argument('-c', '--cooldown', type=int, help='the cooldown time in minutes to reduce noise before any measurement takes place',  action="store")
    parser.add_argument('-p', '--phi', help='list of phi angles to cycle through while datataking', action="append")
    parser.add_argument('-t', '--theta', help='list of theta angles to cycle through while datataking', action="append")
    parser.add_argument('-v', '--HV', help='list of high voltages to cycle through while datataking', action="append")

    args = parser.parse_args()

    if args.outpath:
        OUT_PATH = args.outpath
    if args.loglvl:
        LOG_LVL = args.loglvl
    if args.pmtname:
        PMT_NAME = args.pmtname
    if args.cooldown:
        COOLDOWN_TIME = args.cooldown
    if args.phi:
        PHI_LIST = args.phi
    if args.theta:
        THETA_LIST = args.theta
    if args.HV:
        HV_LIST = args.HV

    main()