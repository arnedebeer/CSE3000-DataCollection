import time
import numpy as np
from serial import Serial
from util import auto_select_serial_port

# Command bytes to send to the device.
MEASUREMENT_START = 0xAB
RECALIBRATE = 0xAC
SET_SAMPLE_RATE = 0xAD

# Default values for measurement.
STANDARD_SAMPLING_RATE = 100 # Note that sampling rate is prone to inaccuracy.
                             # Try to use a multiple of 100 for best results.
STANDARD_DURATION = 1 # Seconds to listen.

class Collector: 
    
    
    def __init__(self, serial_port: str = auto_select_serial_port(), baud_rate: int = 19200) -> None:
        print("Connecting to gesture device at serial port", serial_port, "at baud rate", baud_rate)
        self.connection = Serial(serial_port, baud_rate)
        self.resistance = 0


    def start_measurement(self, duration=STANDARD_DURATION, sampling_rate=STANDARD_SAMPLING_RATE, log=False) -> None:
        print("Starting measurement on device")

        if (self.resistance == 0):
            print("Warning: resistance is not set. Recalibrating.")
            self.recalibrate()
        
        # Set the samping rate.
        self.set_sample_rate(sampling_rate)

        # How many samples we expect to get to fill the time.
        samples = int(duration * sampling_rate)
        print("Sampling for", duration, "seconds at", sampling_rate, "Hz. Expecting", samples, "samples.", "Resistance is", self.resistance, "Ohms.")

        # Send the start measurement command.
        self.write_bytes(MEASUREMENT_START, np.uint32(samples))
    
        # Time we started the measurement.
        start = time.time()

        # Get all measurements samples from the serial port.
        for i in range(samples):
            # Read a line from the serial port.
            # Get the binary result.
            r0 = self.readuint16()
            r1 = self.readuint16()
            r2 = self.readuint16()
            if log:
                print("[Measurement " + str(i) + "] " + str(r0) + ", " + str(r1) + ", " + str(r2))

        diff = time.time() - start
        print("Measurement took", diff, "seconds. (expected " + str(duration) + " seconds)")
        print("Achieved sampling rate of", samples / diff, "Hz. (expected " + str(sampling_rate) + " Hz)  ")

        # Confirm that the measurement is done.
        self.readline(log=True)


    def recalibrate(self) -> None:
        print("Recalibrating light sensitivty of device.")
        self.write_bytes(RECALIBRATE) 
        self.resistance = self.readint()
        print("Resistance set to", self.resistance, "Ohms.")


    def set_sample_rate(self, frequency: int) -> None:
        print("Setting sample frequency to", frequency, "Hz.")
        self.write_bytes(SET_SAMPLE_RATE, np.uint16(frequency))
        self.readline(log=True)

    # Take all arguments and try to send them as bytes over the serial port.
    # Write all the bytes to the serial port.
    def write_bytes(self, *args) -> None:

        # Convert all arguments to bytes.
        all_bytes = list(map(self.to_bytes, list(args)))

        # print(all_bytes)
        # Concatenate all the bytes.
        all_bytes = b"".join(all_bytes)

        # Write the bytes to the serial port.
        self.write(all_bytes)


    def to_bytes(self, arg) -> bytes:
        if isinstance(arg, bytes):
            return arg # It is already bytes.
        
        if isinstance(arg, int):
            # Convert integer to bytes.
            return bytes([arg])
        
        if hasattr(arg, "tobytes"):
            # If from numpy, use the tobytes method.
            return arg.tobytes()
        
        # Just try to send it as bytes.
        return bytes(args)

    def write(self, data) -> None: 
        # print("Will write the following over serial:", data)
        if (self.connection.closed) :
            raise Exception("Serial connection is closed, cannot send data.")
        self.connection.write(data)


    # Reads a single line from the serial port.
    def readline(self, log=False) -> str:
        line = self.connection.readline().decode("utf-8")
        if log:
            print("[Serial] '" + line.strip() + "'")
        return line
    
    def readuint16(self) -> np.uint16:
        number = self.connection.read(2)
        return np.frombuffer(number, dtype=np.uint16)[0]
        # print(number)
        return number #np.uint16(number)


    # Reads an integer on a line from the serial port.    
    def readint(self) -> int:
        return int(self.readline())
    
    # Close the serial connection.
    def close(self) -> None:
        self.connection.close()

    def reset_input_buffer(self) -> None:
        self.connection.reset_input_buffer()



# This is the gesture data that got collected.
# class GestureData:

# If running as script, run this.
if __name__ == "__main__":
    collector = Collector()

    collector.recalibrate()
    collector.set_sample_rate(100)

    collector.start_measurement(sampling_rate=100, duration=10, log=True)
    collector.close()