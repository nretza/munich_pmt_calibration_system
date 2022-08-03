#!/usr/bin/python3
import logging
import time

from serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS # the python serial package
from devices.sim_serial import sim_serial #self written stuff to simulate a serial port

class device:
    """
    Masterclass for all devices
    """
    
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f"{type(self).__name__} initialized")


class serial_device(device):
    """
    Masterclass for serial devices
    """

    def __init__(self, dev, simulating=False, delay=0.1):
        """
        sets up the serial port, simulating and delay
        """

        #self.logger
        super().__init__()

        self.delay = delay
        self.simulating = simulating

        baudrate_dict = {
            "/dev/Laser_control" : 19200,
            "/dev/Picoamp" : 57600,
            "/dev/Powermeter": 38400,
            "/dev/Rotation" : 9600,
            "/dev/HV_Base": 11500
        }
        assert dev in baudrate_dict
        
        # select if serial or sim_serial
        if simulating:
            serial_connection = sim_serial
            self.delay = .01  # set default delay
        else:
            serial_connection = Serial
            self.delay = delay  # set default delay

        # initialise Serial or SimSerial
        self.serial = serial_connection(dev,
                                        baudrate=baudrate_dict[dev],
                                        parity=PARITY_NONE,
                                        stopbits=STOPBITS_ONE,
                                        bytesize=EIGHTBITS,
                                        timeout=2
                                        )

    def serial_io(self, cmd: str, 
                        read_only: bool=False,
                        delay: float=None, 
                        line_ending: str='\r\n',
                        wait_for: str=None,
                        multi_line: bool=False,
                        codec = "utf-8") -> str:

        """
        For communication with the serial port. Flashes buffers of both input and output,
        does command formatting and writes the command to the output buffer.
        After a delay, a line is read from the input buffer and returned.

        PARAMETERS
        ----------
        cmd: Str, bytes, optional
        read_only: only reads line, doesnt write
        delay: float or None, optional
        line_ending: bytes, optional
        wait_for: reads lines consecutively until str is reached
        multiline: reads through serial.readlines()
        """

        # only read, dont write
        if read_only:
            return_str = self.serial.readline()
            self.logger.debug(f'Serial in read only mode. return: {return_str}')
            return return_str.decode()

        # flush buffers
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        # delay override
        if delay is None:
            delay = self.delay

        # encode cmd
        if type(cmd) is str:
            cmd = cmd.encode()
        if not cmd.endswith(line_ending.encode()):
            cmd += line_ending.encode()

        #read and write
        self.serial.write(cmd)
        time.sleep(delay)

        # wait for a set of characters to appear in the output string
        if wait_for:
            while True:
                return_str = self.serial.readline()
                if wait_for in return_str.decode():
                    break
                time.sleep(delay)

        #read everything thats available
        elif multi_line:
            return_str = ""
            return_lst = self.serial.readlines()
            for string in return_lst:
                return_str += string

        #Default: read until a line ending is reached
        else:
            return_str = self.serial.readline()
        self.logger.debug(f'Serial write cmd: {cmd}; return {return_str}')
        return return_str.decode(errors="ignore")
