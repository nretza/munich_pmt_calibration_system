#!/usr/bin/python3
import serial
import logging

from omcu.devices.Serial2 import io_serial


class Rotation:
    """
    Class for the rotation stage consisting of 2 stepper motors
    """
    def __init__(self, dev="/dev/Rotation",  delay=.1):
        self.logger = logging.getLogger(type(self).__name__)
        serial_connection = serial.Serial
        self.delay = delay  # set default delay

        # initialise Serial or SimSerial
        self.serial = serial_connection(dev,
                                        baudrate=9600,  #TODO: change baudrate back, this is currently in the ardunio code!
                                        bytesize=serial.EIGHTBITS,
                                        parity=serial.PARITY_NONE,
                                        timeout=2
                                        )
        #if self.serial.isOpen(): print('ok')
        #else:  print('not ok')

    def set_phi(self, phi):
        """
        Controls the upper stepper. Phi direction is relative to the PMT and not a global coordinate system
        :param phi: Float (0-360 in 5000 steps)
        """
        phi_pos = io_serial(bytes(f'goY {phi}', 'utf-8'), serial=self.serial)
        return phi_pos

    def set_theta(self, theta):
        """
        Controls the lower stepper. Phi direction is relative to the PMT and not a global coordinate system
        :param theta: Float (0-360 in 5000 steps)
        """
        theta_pos = io_serial(bytes(f'goX {theta}', 'utf-8'), serial=self.serial)
        theta_pos = theta_pos/ 5000. * 360 #conversion between steps and degree 360deg = 5000 steps
        return theta_pos
        
    def go_home(self):
        """
        Sends the Rotation stage to home position.
        """
        home_pos = [0, 0]
        home_pos[0] = io_serial(bytes(f'goHomeY', 'utf-8'), serial=self.serial)
        home_pos[1] = io_serial(bytes(f'goHomeX', 'utf-8'), serial=self.serial)
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
        pos[0] = io_serial(bytes(f'getPositionY', 'utf-8'), serial=self.serial)
        pos[1] = io_serial(bytes(f'getPositionX', 'utf-8'), serial=self.serial)
        return pos

    def set_speed(self, speed):
        """
        sets the delay time in-between single steps in milliseconds. Minimum value is 300.
        :param speed: Float (0-360 in 5000 steps)
        """
        speed_val = io_serial(bytes(f'setspeed {speed}', 'utf-8'), serial=self.serial)
        if speed_val > 16383:
            print('the delay might be not accurate anymore.')
        elif speed_val > 32767:
            print('delaytime to large for int. Will produce very short delays')
        return speed_val

    def get_speed(self):
        """
        Returns the delay time in-between single steps in milliseconds. Minimum value is 300.
        """

        speed_val = io_serial(bytes(f'getspeed', 'utf-8'), serial=self.serial)
        return speed_val

    def get_ir(self):
        """
        Returns state of infrared sensor (on=1, off=0)
        """
        ir_val = [0,0]
        ir_val[0] = io_serial(bytes(f'getIRY', 'utf-8'), serial=self.serial)
        ir_val[1] = io_serial(bytes(f'getIRX', 'utf-8'), serial=self.serial)
        # ir_val = io_serial(bytes(f'getIR', 'utf-8'), serial=self.serial)
        return ir_val


if __name__ == "__main__":
    rs = Rotation()
    rs.go_home()
    print('Rotation stage is at home')
