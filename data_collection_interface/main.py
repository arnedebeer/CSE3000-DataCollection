from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QPushButton, QComboBox
import sys
import serial
import time
import matplotlib.pyplot as plt
import pickle
import numpy as np
import os
from util import serial_ports
import threading

# import winsound

CANDIDATE_NUMBER = 1

SAVE_PLOT = True

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

    def __init__(self):
        super(MyWindow,self).__init__()
        self.data = []
        self.chosen_hand = "right_hand"
        self.count = 0
        self.available_ports = serial_ports()
        if len(self.available_ports):
            self.com_port = self.available_ports[0]

        # Change value to select the candidate number
        self.candidate_number = CANDIDATE_NUMBER

        self.initUI()


    def data_button_clicked(self):
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
        self.chosen_hand_button = QPushButton("Right Hand", self)
        self.chosen_hand_button.setCheckable(True)
        self.chosen_hand_button.clicked.connect(self.chosen_hand_button_clicked)
        self.chosen_hand_button.setStyleSheet("background-color : lightgrey")
        general_grid.addWidget(self.chosen_hand_button)

        self.port_dropdown = QComboBox()
        self.port_dropdown.addItems(self.available_ports)
        self.port_dropdown.currentIndexChanged.connect(self.com_port_changed)
        general_grid.addWidget(self.port_dropdown)

        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["Gestures", "Digits", "Letters"])
        self.mode_dropdown.currentIndexChanged.connect(self.mode_change_index_changed)
        general_grid.addWidget(self.mode_dropdown)

        self.control_data_button = QPushButton(self)
        self.control_data_button.setText("control_data")
        # self.control_data_button.clicked.connect(self.data_button_clicked(data_name= "control"))
        general_grid.addWidget(self.control_data_button)

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
        #winsound.Beep(frequency, duration)

        self.count += 1
        print("starting ", self.count)

        # Set the number of samples we collect
        if gesture == "control":
            num_readings = 100
        else:
            num_readings = 500

        # make sure the 'COM#' is set according the Windows Device Manager
        ser = serial.Serial(self.com_port, 19200, timeout=1)

        # Construct data to send over to Arduino
        header = np.uint16(0xAB)
        number = np.uint32(num_readings)
        data = header.tobytes() + number.tobytes()
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
        plt.title(f'candidate {self.candidate_number}')
        plt.show()

        

        # Saving data
        if gesture == "control":
            path = f"src/data_collection/data/{gesture}"
        else:
            path = f"src/data_collection/data/{gesture}/{self.chosen_hand}"

        # Create directory if it doesn't exist yet
        if (not os.path.exists(path)):
            os.makedirs(path)

        data_dict = dict(data = np.array(self.data), gesture = gesture, hand = self.chosen_hand, candidate = self.candidate_number, )

        with open(f"{path}/candidate_{self.candidate_number}.pickle", "ab+") as file:
            # pickle.dump(np.array(self.data), file)
            pickle.dump(data_dict, file)

        if SAVE_PLOT:
            plt.savefig(f"src/data_collection/data/{gesture}/{self.chosen_hand}/candidate_{self.candidate_number}.png")


        print("done ", self.count)


def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())

window()