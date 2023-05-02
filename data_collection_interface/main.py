from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QPushButton, QComboBox, QLineEdit, QLabel, QMessageBox
import sys
import serial
import time
import matplotlib.pyplot as plt
import pickle
import numpy as np
import os
from util import serial_ports
import threading

try:
    import winsound
except ImportError:
    pass

BAUD_RATE = 19200
CANDIDATE_DEFAULT_NUMBER = 1
SAVE_PLOT = True
DATA_ROOT_PATH = "data_collection_interface/data"

# Serial control bits
MEAS_START = 0xAB
REDO_CALIB = 0xAC

class ReadLine:
    def __init__(self, s):  
        self.buf = bytearray()
        self.s = s

    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i + 1]
            self.buf = self.buf[i + 1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i + 1]
                self.buf[0:] = data[i + 1:]
                return r
            else:
                self.buf.extend(data)

class ReadSerial(threading.Thread):
    def __init__(self, serial: serial.Serial):
        super().__init__()
        self.serial = serial

    def run(self) -> None:
        print("Starting serial read thread")
        while not self.serial.closed:
            if self.serial.in_waiting > 0:
                print(self.serial.read_all())


class MyWindow(QMainWindow):
    """Class used for collecting data from candidates.

    The candidate number has to be selected and the Arduino with the three photodiodes must be connected with the
    appropriate com port selected.
    When run, a window will appear for every gesture. Once a button is clicked, the samples will be collected and saved
    into the appropriate pickle file.
    """

    com_port = None

    def __init__(self):
        super(MyWindow,self).__init__()
        self.data = []
        self.chosen_hand = "right_hand"
        self.count = 0
        self.available_ports = serial_ports()

        if len(self.available_ports):
            self.com_port = self.available_ports[0]

        # Change value to select the candidate number
        self.candidate_identifier = str(CANDIDATE_DEFAULT_NUMBER)

        self.initUI()


    def data_button_clicked(self):
        if self.com_port is None:
            msg = QMessageBox()
            msg.setText("No COM port selected for serial connection...")
            msg.exec()
        else:
            self.view(self.sender().text())

    # method called by button
    def chosen_hand_button_clicked(self):
        if self.chosen_hand_button.isChecked():
            self.chosen_hand_button.setStyleSheet("background-color : lightblue")
            self.chosen_hand_button.setText("Left Hand")
            self.chosen_hand = "left_hand"

        else:
            self.chosen_hand_button.setStyleSheet("background-color : lightgrey")
            self.chosen_hand_button.setText("Right Hand")
            self.chosen_hand = "right_hand"

    def mode_change_index_changed(self, changedToIndex):
        self.activeFrame.hide()
        self.frames[changedToIndex].show()
        self.activeFrame = self.frames[changedToIndex]

    def com_port_changed(self, changedToIndex):
        self.com_port = self.available_ports[changedToIndex]

    def candidate_text_changed(self, changedTo):
        self.candidate_identifier = changedTo

    def redo_calibration(self):
        s = serial.Serial(self.com_port, BAUD_RATE, timeout=1)
        s.write(np.uint16(REDO_CALIB).tobytes())
        s.close()

    def initUI(self):
        # Connecting quit function
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

        # QT display
        w = QtWidgets.QWidget()
        self.setCentralWidget(w)
        self.setGeometry(200, 200, 300, 300)

        general_grid = QtWidgets.QGridLayout(w)

        # General buttons
        self.port_dropdown = QComboBox()
        self.port_dropdown.addItems(self.available_ports)
        self.port_dropdown.currentIndexChanged.connect(self.com_port_changed)
        general_grid.addWidget(self.port_dropdown)

        self.calibration_button = QPushButton("Redo calibration", self)
        self.calibration_button.clicked.connect(self.redo_calibration)
        self.calibration_button.setStyleSheet("background-color : red; color: white")
        general_grid.addWidget(self.calibration_button)

        general_grid.addWidget(QLabel("Candidate identifier:"))
        self.candidate_textfield = QLineEdit()
        self.candidate_textfield.setText(self.candidate_identifier)
        self.candidate_textfield.textChanged.connect(self.candidate_text_changed)
        general_grid.addWidget(self.candidate_textfield)

        self.control_data_button = QPushButton(self)
        self.control_data_button.setText("control_data")
        self.control_data_button.clicked.connect(self.data_button_clicked)
        general_grid.addWidget(self.control_data_button)
        
        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["Gestures", "Digits", "Letters"])
        self.mode_dropdown.currentIndexChanged.connect(self.mode_change_index_changed)
        general_grid.addWidget(self.mode_dropdown)

        self.chosen_hand_button = QPushButton("Right Hand", self)
        self.chosen_hand_button.setCheckable(True)
        self.chosen_hand_button.clicked.connect(self.chosen_hand_button_clicked)
        self.chosen_hand_button.setStyleSheet("background-color : lightgrey")
        general_grid.addWidget(self.chosen_hand_button)

        gestures = ["swipe_left", "swipe_right", "swipe_up", "swipe_down", "clockwise", "counter_clockwise", "tap", "double_tap", "zoom_in", "zoom_out"]
        digits = [("digit_"+str(i)) for i in range(10)]
        characters = [("char_" + chr(i)) for i in range(ord('A'), ord('J')+1)]

        #Grids
        gestures_frame = self.generate_frame(gestures)
        digits_frame = self.generate_frame(digits)
        characters_frame = self.generate_frame(characters)

        #put grids in global object
        self.frames = [gestures_frame, digits_frame, characters_frame]

        #Hide frames not used first
        self.activeFrame = gestures_frame
        digits_frame.hide()
        characters_frame.hide()

        general_grid.addWidget(gestures_frame)
        general_grid.addWidget(digits_frame)
        general_grid.addWidget(characters_frame)

        


    def generate_frame(self, grid_items):
        grid = QtWidgets.QGridLayout()
        # Initialize buttons on display

        for label in grid_items:
            button = QPushButton(self)
            button.setText(label)
            button.clicked.connect(self.data_button_clicked)
            grid.addWidget(button)
        
        frame = QtWidgets.QFrame()
        frame.setLayout(grid)
        return frame

    def closeEvent(self, event):
        event.accept()

    def view(self, gesture):
        
        # Select frequency and duration of beep
        frequency = 500  # Set Frequency To 2500 Hertz
        duration = 500  # Set Duration To 1000 ms == 1 second

        if winsound is not None:
            winsound.Beep(frequency, duration)

        self.count += 1
        print("starting ", self.count)

        # Set the number of samples we collect
        if gesture == "control_data":
            num_readings = 1000
        else:
            num_readings = 500

        ser = serial.Serial(self.com_port, BAUD_RATE, timeout=1)

        # Construct data to send over to Arduino
        header = np.uint16(MEAS_START)
        number = np.uint32(num_readings)
        data = header.tobytes() + number.tobytes()
        print(len(data))
        ser.write(bytes(data))
        
        # The first value we get back is the calibration value
        while not ser.closed and ser.in_waiting == 0:
            pass

        resistor_value = ser.readline()
        print("The resistor value is: %s" % int(resistor_value))
        
        reader = ReadLine(ser)
        time.sleep(2)

        # Sampling the data
        self.data = []
        for i in range(num_readings):
            line = reader.readline()  # read a byte string
            if line:
                string = line.decode().strip("\n")  # convert the byte string to a unicode string
                t = list(map(int, string.split(", ")))
                self.data.append(t)  # add int to data list
        ser.close()

        # build the plot
        plt.plot(self.data)
        plt.xlabel('Time')
        plt.ylabel('Photodiode Reading')
        plt.title(f'candidate {self.candidate_identifier}')
        plt.show()

        # Saving data
        if gesture == "control":
            path = os.path.join(DATA_ROOT_PATH, gesture)
        else:
            path = os.path.join(DATA_ROOT_PATH, gesture, self.chosen_hand)

        # Create directory if it doesn't exist yet
        if not os.path.exists(path):
            os.makedirs(path)

        data_dict = {
            'data': np.array(self.data),
            'gesture': gesture,
            'hand': self.chosen_hand,
            'candidate': self.candidate_identifier,
            'resistor_value': resistor_value
        }

        with open(os.path.join(path, f"candidate_{self.candidate_identifier}.pickle"), "ab+") as file:
            pickle.dump(data_dict, file)

        if SAVE_PLOT:
            plt.savefig(os.path.join(path, f"candidate_{self.candidate_identifier}_{self.count}.png"))


        print("done ", self.count)


def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())

window()