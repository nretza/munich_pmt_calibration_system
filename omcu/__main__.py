#!/usr/bin/python3
import os
import argparse
import time
import importlib.machinery
import importlib.util

from devices.Picoscope import Picoscope
from devices.PSU import PSU0, PSU1
from devices.Picoamp import Picoamp
from devices.Rotation import Rotation
from devices.Laser import Laser
from devices.Powermeter import Powermeter

from utils.util import *
from utils.testing_procedure import *

from data_analysis.Data_Analysis import Data_Analysis


#TODO: implement and test HV base
#TODO: device controls at start of every function


##########################################################################################
##########################################################################################
##########################################################################################


def main():


    # check that outdir exists
    if not os.path.exists(OUT_PATH):
        raise FileNotFoundError(f"ERROR: given path {OUT_PATH} does not exist! Please adjust in config.py.")
    #set pmt_name and datapath (either by user or config)
    if not PMT_NAME:
        pmt_name = input("Please enter the Name of the PMT inside the OMCU:\n>>> ")
    else:
        pmt_name = PMT_NAME
    DATA_PATH = os.path.join(OUT_PATH, pmt_name)
    while os.path.exists(DATA_PATH):
        pmt_name = input("ERROR: given PMT name seems to have Data stored already! Please choose another name:\n>>> ")
        DATA_PATH = os.path.join(OUT_PATH, pmt_name)
    os.mkdir(DATA_PATH)
    #setup logging
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
    check = input("Please confirm that the OMCU is properly set up [Yes/no]:\n>>> ")
    if not (check.lower() == "yes" or check.lower() == "y"):
        print("ERROR: OMCU determined as not set up by user input. Exiting program. Good bye!")
        exit()

    start_time = time.time()

    #Turn relevant devices on
    print()
    try:
        print("connecting PSU1")
        PSU1.Instance().on()
    except:
        print(f"\nERROR:\t PSU_1 could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(101)
    try:
        print("connecting Rotation Stage")
        Rotation.Instance().go_home()
    except:
        print(f"\nERROR:\t Rotation Stage could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(102)
    try:
        print("connecting Laser")
        Laser.Instance()
    except:
        print(f"\nERROR:\t Laser could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(103)
    try:
        print("connecting HV supply")
        HV_supply.Instance().on()
    except:
        print(f"\nERROR:\t HV_supply could not be connected to successfully.\n \
        Please make sure the device is turned on by the hands of an electronic expert and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(104)
    try:
        print("connecting Powermeter")
        Powermeter.Instance()
    except:
        print(f"\nERROR:\t Powermeter could not be connected to successfully.\n \
        Please make sure the device is turned on by the hands of an electronic expert and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(105)


    #time to reduce noise
    print(f"\nOMCU turned on successfully. Entering cooldown time of {COOLDOWN_TIME} minutes before taking measurements")
    Laser.Instance().off_pulsed()
    for i in range(COOLDOWN_TIME):
        remain = COOLDOWN_TIME - i
        print(f"{remain} minutes of cooldown remaining")
        time.sleep(60)
    Laser.Instance().on_pulsed()
    print("cooldown completed!")

    #testing protocols
    if config.PHOTOCATHODE_SCAN:
        tune_parameters("from_config")
        photocathode_scan(DATA_PATH)
    if config.FRONTAL_HV_SCAN:
        tune_parameters("from_config")
        frontal_HV_scan(DATA_PATH)

    
    #turn devices off
    HV_supply.Instance().off_all()
    Laser.Instance().off_pulsed()
    PSU1.Instance().off()

    print("finished data taking")

    if config.ANALYSIS_PERFORM:
        print("analyzing data now")
        analysis = Data_Analysis(DATA_PATH)
        if config.FRONTAL_HV_SCAN:
            analysis.analyze_FHVS()
        if config.PHOTOCATHODE_SCAN:
            analysis.analyze_PCS()

    end_time = time.time()

    print("\nEnd of program reached, nothing to execute anymore.")
    print(f"Total execution time: {round((end_time - start_time)/60,0)} minutes")
    print("\nPLEASE MAKE SURE TO TURN ALL DEVICES OFF BEFORE OPENING THE OMCU!\nGood bye!\n")
    exit(0)


##########################################################################################
##########################################################################################
##########################################################################################


if __name__ == "__main__":

    print("""
     ______   __       __   ______   __    __ 
    /      \ |  \     /  \ /      \ |  \  |  \ 
   |  $$$$$$\| $$\   /  $$|  $$$$$$\| $$  | $$
   | $$  | $$| $$$\ /  $$$| $$   \$$| $$  | $$
   | $$  | $$| $$$$\  $$$$| $$      | $$  | $$
   | $$  | $$| $$\$$ $$ $$| $$   __ | $$  | $$
   | $$__/ $$| $$ \$$$| $$| $$__/  \| $$__/ $$
    \$$    $$| $$  \$ | $$ \$$    $$ \$$    $$
     \$$$$$$  \$$      \$$  \$$$$$$   \$$$$$$ 
                                       
                                           
       Optical Module Calibration Unit
              (control software)
           
   -----------------------------------------
    by: Niklas Retza (niklas.retza@tum.de)
                 July 2022
   -----------------------------------------
    """)

    parser = argparse.ArgumentParser(   description='Control Software fpr the Optical Module Calibration Unit.',
                                        add_help=True,
                                        epilog= """
                                                Please regard the config file omcu/config.py for further settings not passed through command line arguments.
                                                In case you need further help, please contact the author: niklas.retza@tum.de
                                                 """)

    parser.add_argument('-o', '--outpath',  help='path to the program output',  action="store")
    parser.add_argument('-l', '--loglvl', help='the logging level for the log output file', action="store")
    parser.add_argument('-n', '--pmtname',  help='name of the PMT inside the omcu',  action="store")
    parser.add_argument('-c', '--cooldown', type=int, help='the cooldown time in minutes to reduce noise before any measurement takes place',  action="store")
    parser.add_argument('-s', '--config', type=str, help="path to an alternative config file, which should be used instead of the default one", action="store")
    parser.add_argument('--printconfig', help="prints the content of the given config file. Exits the program afterwards.", action="store_true")
    
    args = parser.parse_args()

    if args.printconfig:
        #if --printconfig is called, prints config, then exits programm
        if args.config:
            filepath = args.config
        else:
            filepath = os.path.join(os.getcwd(), "omcu" ,"config.py")
        try:
            with open(filepath) as file:
                print(f"\nContent of config file {filepath}:\n")
                print(file.read())
        except:
            print(f"Error while handling config file {filepath}. Does it exist?\nAborting\nGood Bye!")
            exit(201)
        exit(0)

    if args.config:
        #override default config imoport if --config is called
        try:
            loader = importlib.machinery.SourceFileLoader("config.py", args.config)
            spec = importlib.util.spec_from_loader("config.py", loader)
            config = importlib.util.module_from_spec(spec)
            loader.exec_module(config)
        except:
            print(f"WARNING: Failed to import config file at {args.config}.\nWill import default config file.")
            import config
    else: 
        import config

    # config imports
    OUT_PATH    = config.OUT_PATH
    PMT_NAME    = config.PMT_NAME
    LOG_FILE    = config.LOG_FILE
    LOG_LVL     = config.LOG_LVL

    COOLDOWN_TIME = config.COOLDOWN_TIME

    # override by command line arguments
    if args.outpath:
        OUT_PATH = args.outpath
    if args.loglvl:
        LOG_LVL = args.loglvl
    if args.pmtname:
        PMT_NAME = args.pmtname
    if args.cooldown:
        COOLDOWN_TIME = args.cooldown

    main()
