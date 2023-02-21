#!/usr/bin/python3
import time

from devices.device import serial_device
from devices.PSU import PSU1


class Rotation(serial_device):
    
    """
    Class for the rotation stage consisting of 2 stepper motors
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = Rotation()
        return cls._instance

    def __init__(self, dev="/dev/Rotation",  delay=0.1):

        if Rotation._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            Rotation._instance = self

        super().__init__(dev, delay=delay)

        #soemhow the first i/o on the RS is always buggy. Sennd dummy message to avoid bugs
        self.serial_io(' ')

    def set_phi(self, phi):
        """
        Controls the upper stepper. Phi direction is relative to the PMT and not a global coordinate system
        :param phi: Float (0-360 in 5000 steps)
        """
        PSU1.Instance().on()
        self.logger.info(f"rotating to phi: {phi}")
        phi_pos = self.serial_io(f'goY {phi}', wait_for=": ").split(':')[1]
        time.sleep(0.2)
        PSU1.Instance().off()
        return float(phi_pos)

    def set_theta(self, theta):
        """
        Controls the lower stepper. Phi direction is relative to the PMT and not a global coordinate system
        :param theta: Float (0-360 in 5000 steps)
        """
        PSU1.Instance().on()
        self.logger.info(f"rotating to theta: {theta}")
        theta_pos = self.serial_io(f'goX {theta}', wait_for=": ").split(':')[1]
        time.sleep(0.2)
        PSU1.Instance().off()
        return float(theta_pos) / 5000. * 360 #conversion between steps and degree 360deg = 5000 steps
        
    def go_home(self):
        """
        Sends the Rotation stage to home position.
        """
        PSU1.Instance().on()
        home_pos = [0,0]
        hpY = self.serial_io(f'goHomeY', wait_for=": ").split(':')[1]
        hpX = self.serial_io(f'goHomeX', wait_for=": ").split(':')[1]
        home_pos[0] = float(hpY)
        home_pos[1] = float(hpX)
        self.logger.info(f"returning to home position: {home_pos}")
        time.sleep(0.2)
        PSU1.Instance().off()
        return home_pos

    def set_position(self, phi, theta):
        """
        Gives the rotation stage 2D coordinates to move to. First phi, than theta direction
        :param phi: Float (0-360 in 5000 steps)
        :param theta: Float (0-360 in 5000 steps)
        """
        pos = [0, 0]
        pos[0] = self.set_phi(phi)
        pos[1] = self.set_theta(theta)
        return pos

    def get_position(self):
        """
        Returns the current position
        """
        pos = [0, 0]
        posY = self.serial_io(f'getPositionY', wait_for=": ").split(':')[1]
        posX = self.serial_io(f'getPositionX', wait_for=": ").split(':')[1]
        pos[0] = float(posY)
        pos[1] = float(posX)
        return pos

    def set_speed(self, speed):
        """
        sets the delay time in-between single steps in milliseconds. Minimum value is 300.
        :param speed: Float (0-360 in 5000 steps)
        """
        self.logger.info(f"setting rotation speed to {speed}")
        speed_str = self.serial_io(f'setspeed {speed}', wait_for=": ").split(':')[1]
        speed_val = float(speed_str)
        if speed_val > 16383:
            self.logger.warning(f"speed {speed_val} too high, the delay might be not accurate anymore.")
            print('the delay might be not accurate anymore.')
        elif speed_val > 32767:
            self.logger.warning(f"speed {speed_val} too high, delaytime to large for int. Will produce very short delays.")
            print('delaytime to large for int. Will produce very short delays')
        return speed_val

    def get_speed(self):
        """
        Returns the delay time in-between single steps in milliseconds. Minimum value is 300.
        """
        speed_str = self.serial_io('getspeed', wait_for=": ").split(':')[1]
        speed_val = float(speed_str)
        return speed_val

    def get_ir(self):
        """
        Returns state of infrared sensor (on=1, off=0)
        """
        ir_val = [0,0]
        irY = self.serial_io('getIRY', wait_for=": ").split(':')[1]
        irX = self.self.serial_io('getIRX', wait_for=": ").split(':')[1]
        ir_val[0] = float(irY)
        ir_val[1] = float(irX)
        return ir_val