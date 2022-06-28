import serial
import time

ser = serial.Serial(port = '/dev/Rotation', baudrate = 9600, parity = serial.PARITY_NONE, bytesize = serial.EIGHTBITS, timeout=2) #stopbits = serial.STOPBITS_ONE
    
ser.write(bytes(f'goX 30', 'utf-8'))
time.sleep(10)
ser.write(bytes(f'goHomeX', 'utf-8'))
time.sleep(10)
print(serial.VERSION)
print(serial.in_waiting)
byteData = ser.read(size=serial.in_waiting)
print(byteData)

