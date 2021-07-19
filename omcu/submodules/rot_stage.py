#!/usr/bin/python3
import serial
import logging
import time
from Serial2 import io_serial

class Rotation_stage:
    """
    Class for the rotation stage consisting of 2 stepper motors
    """
    def __init__(self, dev="/dev/ttyUSB0",  delay=.1): #TODO: Change device path!
        self.logger = logging.getLogger(type(self).__name__)
        serial_connection = serial.Serial
        self.delay = delay  # set default delay

        # initialise Serial or SimSerial
        self.serial = serial_connection(dev,
                                        baudrate=9600, #TODO: change baudrate back, this is currently in the ardunio code!
                                        bytesize=serial.EIGHTBITS,
                                        parity=serial.PARITY_NONE,
                                        timeout=2
                                        )
        
    def go_phi(self,phi):
        """
        Controls the upper stepper. Phi direction is relativ to the PMT and not a global coordinate system

        PARAMETERS
        ----------
        phi: Float
        """
        
        ret = io_serial(bytes(f'goY {phi}', 'utf-8'), serial=self.serial)
        return ret
        
        
    def go_theta(self,theta):
        """
        Controls the lower stepper. Phi direction is relativ to the PMT and not a global coordinate system

        PARAMETERS
        ----------
        phi: Float
        """
        return io_serial(bytes(f'goX {theta}', 'utf-8'), serial=self.serial)
        
    def go_home(self):
        """
        sends gohome command
        """
        ret = [0,0]
        ret[0] = io_serial(bytes(f'goHomeY', 'utf-8'), serial=self.serial)
        ret[1] = io_serial(bytes(f'goHomeX', 'utf-8'), serial=self.serial)
        return ret
    
    def set_speed(self,speed):
        """
        sets the delaytime inbetween single steps in milliseconds. Minimum value is 300.
        PARAMETERS
        ----------
        speed: Float
        """
        return io_serial(bytes(f'setspeed {speed}', 'utf-8'), serial=self.serial)
        
    def scan(self,phi,theta):
        """
        Gives the rotation stage 2D coordinates to move to. First phi, than theta direction
        PARAMETERS
        ----------
        phi: Float
        theta: Float
        """
        ret = [0,0]
        ret[0] = self.go_phi(phi)
        ret[1] = self.go_theta(theta)
        return ret
    
    def get_position(self):
        """
        Returns the current position
        """
        ret = [0,0]
        ret[0] = io_serial(bytes(f'getPositionY', 'utf-8'), serial=self.serial)
        ret[1] = io_serial(bytes(f'getPositionX', 'utf-8'), serial=self.serial)
        return ret
        
    def get_speed(self):
        """
        Returns the current position
        """
        return io_serial(bytes(f'getspeed', 'utf-8'), serial=self.serial)
    
    '''def __write_serial(self, cmd, delay=None, line_ending=b'\r\n'):  # "__" : private function for this class### needed, why can't import?!
        """

        PARAMETERS
        ----------
        cmd: Str, bytes, optional
        delay: float or None, optional
        line_ending: bytes, optional
        """
        if delay is None:
            delay = self.delay

        if type(cmd) is str:
            cmd = cmd.encode()

        if not cmd.endswith(line_ending):
            cmd += line_ending

        self.serial.write(cmd)
        time.sleep(delay)

        while True:
            return_str = self.serial.readline().decode()
            self.logger.debug(f'Serial write cmd: {cmd}; return {return_str}')
            return return_str
    '''
    
    '''def io_serial(self, cmd, delay=None):
        """
        1. Checks if something is to read. 2. write command to serial 3. checks if response is available and if yes: prints it
        PARAMETERS
        ----------
        cmd: bytes
        delay: float or None
        """
        if self.serial.in_waiting:
            print(self.serial.read_until(size=self.serial.in_waiting))
        
        if delay is None:
            delay = self.delay
            
        self.serial.write(cmd)
        
        while True:
            if self.serial.in_waiting > 0:
                print(self.serial.read(size=self.serial.in_waiting)[:-2])
                break
            time.sleep(delay)
      '''  
        
     
