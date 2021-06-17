#!/usr/bin/python3
import serial
import time

def io_serial(cmd, delay=0.1,serial=serial):
        """
        1. Checks if something is to read. 2. write command to serial 3. checks if response is available and if yes: prints it
        PARAMETERS
        ----------
        cmd: bytes
        delay: float or None
        """
        if serial.in_waiting:
            print(serial.read_until(size=serial.in_waiting))
        
        serial.write(cmd)
        
        while True:
            if serial.in_waiting > 0:
                print(serial.read(size=serial.in_waiting)[:-2])
                break
            time.sleep(delay)
