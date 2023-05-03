# 
# sample_rate.py
# A script to calculate the maximum sampling rate of the device.
# Script on device should not have a delay between sending data for this to work.
#

import serial
import time
import platform
import sys

def os_serial_port():
    # Get the operating system
    os = platform.system()
    if os == "Windows":
        return "COM3"
    elif os == "Linux":
        return "/dev/ttyACM0"
    elif os == "Darwin":
        return "/dev/tty.usbmodem211201"

SERIAL_PORT = os_serial_port()
    
def calculate_sampling_rate():

    duration = 10 # Duration to sample for in seconds
    print("Sampling for", duration, "seconds.")

    # Connect with the device and read the data
    ser = serial.Serial(SERIAL_PORT, 19200, timeout=duration)
    bytes = ser.read(sys.maxsize) # read until the timeout

    # Convert the bytes to a string and split on newlines
    lines = bytes.decode('utf-8').split('\n')
    print("Lines received from device:", len(lines))
    
    # remove the first line and last line (since it could be not complete)
    lines = lines[1:-1]

    # Calculate the sampling rate
    sampling_rate = len(lines) / duration
    print("Sampling rate: ", sampling_rate, "Hz")

    # Print the first two lines:
    print("\nFirst two lines:")
    for i in range(2):
        print(lines[i])


    print("\nLast two lines:")
    # Print the last two lines:
    for i in range(len(lines)-2, len(lines)):
        print(lines[i])

    ser.close()

    
if __name__ == "__main__":
    calculate_sampling_rate()