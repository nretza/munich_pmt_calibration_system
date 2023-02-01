#!/usr/bin/python3

import os
import argparse
import logging
import time
import importlib.machinery
import importlib.util

from devices.Picoscope import Picoscope
from devices.PSU import PSU1
from devices.Rotation import Rotation
from devices.Laser import Laser
from devices.Powermeter import Powermeter
from devices.uBase import uBase

from utils.util import setup_file_logging
from utils.TestingProcedures import photocathode_scan, frontal_HV_scan, charge_linearity_scan, dark_count_scan
from utils.DataAnalysis import DataAnalysis


##########################################################################################
##########################################################################################
##########################################################################################


def main():


    # check that outdir exists
    if not os.path.exists(OUT_PATH):
        raise FileNotFoundError(f"ERROR: given path '{OUT_PATH}' does not exist! Please adjust in config.py.")
        
    # set pmt_name and datapath (either by user or config)
    if not PMT_NAME:
        pmt_name = input("Please enter the Name of the PMT inside the OMCU:\n>>> ")
    else:
        pmt_name = PMT_NAME

    # check that datapath does not already exists (no data is overwritten)
    DATA_PATH = os.path.join(OUT_PATH, pmt_name)
    while os.path.exists(DATA_PATH):
        pmt_name = input("ERROR: given PMT name seems to have Data stored already! Please choose another name:\n>>> ")
        DATA_PATH = os.path.join(OUT_PATH, pmt_name)
    os.makedirs(DATA_PATH)

    # setup logging
    setup_file_logging(logging_file=os.path.join(DATA_PATH,LOG_FILE), logging_level=LOG_LVL)
    logging.getLogger("OMCU").info(f"--- OMCU INITIALIZING ---")
    logging.getLogger("OMCU").info(f"storing data in {DATA_PATH}")


    # user input to confirm device setup    
    print("\nPlease make sure that the following conditions are met before the OMCU is turned on:\n")
    print("1.)\tThe PMT is connected to the Picoscope via the coaxial cable labeled \"Signal\" inside the OMCU.")
    print("2.)\tThe OMCU is properly closed and the red handles are shut.")
    print("3.)\the uBase is plugged in. (See plug to the right of the OMCU)")
    print("4.)\tThe following devices to the right of the OMCU are turned on:")
    print("\t\t - the Power Meter")
    print("\t\t - the Laser Control System")
    print("\t\t - both PSU_0 and PSU_1")
    print("\t\t - the Picoscope")
    print("\t\t - the Picoamp")
    print()
    check = input("Please confirm that the OMCU is properly set up [Yes/no]:\n>>> ")
    if not (check.lower() == "yes" or check.lower() == "y"):
        print("ERROR: OMCU determined as not set up by user input. Exiting program. Good bye!")
        exit()
    logging.getLogger("OMCU").info(f"omcu marked as set up by user. Performing checks...")
    start_time = time.time()

    #Turn relevant devices on
    print()
    try:
        print("connecting PSU1")
        PSU1.Instance().off()
        logging.getLogger("OMCU").info(f"PSU1 functional")
    except:
        print(f"\nERROR:\t PSU_1 could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(101)
    try:
        print("connecting Rotation Stage")
        Rotation.Instance().go_home()
        logging.getLogger("OMCU").info(f"rotation stage functional")
    except:
        print(f"\nERROR:\t Rotation Stage could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(102)
    try:
        print("connecting Laser")
        Laser.Instance().off_pulsed()
        logging.getLogger("OMCU").info(f"laser functional")

    except:
        print(f"\nERROR:\t Laser could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(103)
    try:
        print("connecting Powermeter")
        Powermeter.Instance()
        logging.getLogger("OMCU").info(f"powermeter functional")
    except:
        print(f"\nERROR:\t Powermeter could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(105)
    try:
        print("connecting Picoscope")
        Picoscope.Instance()
        logging.getLogger("OMCU").info(f"picoscope functional")
    except:
        print(f"\nERROR:\t Picoscope could not be connected to successfully.\n \
        Please make sure the device is turned on and properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(106)
    try:
        print("connecting uBase")
        assert uBase.Instance().getUID() == "0056006b 344b5009 20333353"
        logging.getLogger("OMCU").info(f"uBase functional")
    except:
        print(f"\nERROR:\t uBase could not be connected to successfully.\n \
        Please make sure the device is properly connected.\n \
        Consider the logging file in {DATA_PATH} for further help")
        print("\n exiting program now. Good bye!")
        exit(107)

    # time to reduce noise
    print(f"\nOMCU turned on successfully. Entering cooldown time of {COOLDOWN_TIME} minutes before taking measurements")
    logging.getLogger("OMCU").info(f"entering cooldown time of {COOLDOWN_TIME} minutes")
    Laser.Instance().off_pulsed()
    uBase.Instance().SetVoltage(config.COOLDOWN_HV)
    halftime_reached = False
    for i in range(COOLDOWN_TIME):
        remain = COOLDOWN_TIME - i
        print(f"{remain} minutes of cooldown remaining")
        if remain <= COOLDOWN_TIME/2 and not halftime_reached:
            print("reached cooldown halftime, turning laser on")
            halftime_reached = True
            Laser.Instance().on_pulsed()
        time.sleep(60)
    Laser.Instance().off_pulsed()
    print("cooldown completed!")
    logging.getLogger("OMCU").info(f"cooldown completed")


    # testing protocols
    if config.PHOTOCATHODE_SCAN:
        photocathode_scan(DATA_PATH)
    if config.FRONTAL_HV_SCAN:
        frontal_HV_scan(DATA_PATH)
    if config.CHARGE_LINEARITY_SCAN:
        charge_linearity_scan(DATA_PATH)
    if config.DARK_COUNT_SCAN:
        dark_count_scan(DATA_PATH)


    
    # turn devices off
    Laser.Instance().off_pulsed()
    uBase.Instance().SetVoltage(10)
    Rotation.Instance().go_home()
    PSU1.Instance().off()


    print("finished data taking")

    if config.ANALYSIS_PERFORM:
        print("analyzing data now")
        analysis = DataAnalysis(DATA_PATH)
        if config.FRONTAL_HV_SCAN:
            analysis.analyze_FHVS()
        if config.PHOTOCATHODE_SCAN:
            analysis.analyze_PCS()
        if config.CHARGE_LINEARITY_SCAN:
            analysis.analyze_CLS()
        if config.DARK_COUNT_SCAN:
            analysis.analyze_DCS()

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
                 January 2023
   -----------------------------------------
    """)

    parser = argparse.ArgumentParser(description='Control Software fpr the Optical Module Calibration Unit.',
                                     add_help=True,
                                     epilog="""
                                               Please regard the config file omcu/config.py for further settings not passed through command line arguments.
                                               In case you need further help, please contact the author: niklas.retza@tum.de
                                               """)

    parser.add_argument('-o', '--outpath',  help='path to the program output',  action="store")
    parser.add_argument('-l', '--loglvl', help='the logging level for the log output file', action="store")
    parser.add_argument('-n', '--pmtname',  help='name of the PMT inside the omcu',  action="store")
    parser.add_argument('-c', '--cooldown', type=int, help='the cooldown time in minutes to reduce noise before any measurement takes place',  action="store")
    parser.add_argument('--config', type=str, help="path to an alternative config file, which should be used instead of the default one", action="store")
    parser.add_argument('--script', type=str, help="executes the given script instead of the main program.", action="store")
    parser.add_argument('--printconfig', help="prints the content of the given config file. Exits the program afterwards.", action="store_true")
    
    args = parser.parse_args()

    if args.script:
        #if --script is called, run script instead of main routine
        if os.path.isfile(args.script) and os.path.splitext(args.script)[1] == ".py":
            with open(args.script) as f:
                check = input(f"WARNING: You are about to run {args.script} instead of the usual OMCU routine.\nProceed? [Y/N]")
                if (check.lower() == "yes" or check.lower() == "y"):
                    print(f"executing {args.script}:\n")
                    code = compile(f.read(), args.script, 'exec')
                    exec(code)
                    exit(0)
                else:
                    print("user abort,\nGoodbye!")
                    exit(0)
        else:
            print("Error, please pass a proper Python file to --script!")
            exit(0)

    if args.printconfig:
        #if --printconfig is called, prints config, then exits programm
        if args.config:
            filepath = args.config
        else:
            filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.py")
        try:
            with open(filepath) as file:
                print(f"\nContent of config file {filepath}:\n")
                print(file.read())
        except:
            print(f"Error while handling config file {filepath}. Does it exist?\nAborting\nGood Bye!")
            exit(201)
        exit(0)

    if args.config:
        #override default config import if --config is called
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
