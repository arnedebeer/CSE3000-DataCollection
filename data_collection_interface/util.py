import sys
import glob
import serial
import platform

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def auto_select_serial_port() -> str:
    ports = serial_ports()
    os = platform.system()
    if os == "Windows":
        return ports[0]
    elif os == "Linux":
        return ports[0]
    elif os == "Darwin":
        # Try to find the port that has usbmoddem in it
        for port in ports:
            if "usbmodem" in port:
                return port
    
    return ports[0] # Otherwise just return the first port
    