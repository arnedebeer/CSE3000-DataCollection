from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QPushButton
import sys
import serial
import time
import matplotlib.pyplot as plt
import pickle
import numpy as np
import winsound
import os


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


class MyWindow(QMainWindow):
    """Class used for collecting data from candidates.

    The candidate number has to be selected and the Arduino with the three photodiodes must be connected with the
    appropriate com port selected.
    When run, a window will appear for every gesture. Once a button is clicked, the samples will be collected and saved
    into the appropriate pickle file.
    """

    def __init__(self):
        super(MyWindow,self).__init__()
        self.initUI()
        self.data = []
        self.chosen_hand = "right_hand"
        self.count = 0

        # Change value to select the candidate number
        self.candidate_number = 1

    def control_data_button_clicked(self):
        self.view("control")

    def swipe_left_button_clicked(self):
        self.view("swipe_left")

    def swipe_right_button_clicked(self):
        self.view("swipe_right")

    def swipe_up_button_clicked(self):
        self.view("swipe_up")

    def swipe_down_button_clicked(self):
        self.view("swipe_down")

    def clockwise_button_clicked(self):
        self.view("clockwise")

    def counterclockwise_button_clicked(self):
        self.view("counterclockwise")

    def tap_button_clicked(self):
        self.view("tap")

    def double_tap_button_clicked(self):
        self.view("double_tap")

    def zoom_in_button_clicked(self):
        self.view("zoom_in")

    def zoom_out_button_clicked(self):
        self.view("zoom_out")

    # method called by button
    def chosen_hand_button_clicked(self):

        # if button is checked
        if self.chosen_hand_button.isChecked():

            # setting background color to light-blue
            self.chosen_hand_button.setStyleSheet("background-color : lightblue")
            self.chosen_hand_button.setText("Left Hand")
            self.chosen_hand = "left_hand"

        # if it is unchecked
        else:

            # set background color back to light-grey
            self.chosen_hand_button.setStyleSheet("background-color : lightgrey")
            self.chosen_hand_button.setText("Right Hand")
            self.chosen_hand = "right_hand"

    def initUI(self):
        # Connecting quit function
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

        # QT display
        w = QtWidgets.QWidget()
        self.setCentralWidget(w)
        grid = QtWidgets.QGridLayout(w)

        # Initialize buttons on display
        self.setGeometry(200, 200, 300, 300)
        self.chosen_hand_button = QPushButton("Right Hand", self)
        self.chosen_hand_button.setCheckable(True)
        self.chosen_hand_button.clicked.connect(self.chosen_hand_button_clicked)
        self.chosen_hand_button.setStyleSheet("background-color : lightgrey")
        grid.addWidget(self.chosen_hand_button)

        self.control_data_button = QPushButton(self)
        self.control_data_button.setText("control_data")
        self.control_data_button.clicked.connect(self.control_data_button_clicked)
        grid.addWidget(self.control_data_button)

        self.swipe_left_button = QPushButton(self)
        self.swipe_left_button.setText("swipe_left")
        self.swipe_left_button.clicked.connect(self.swipe_left_button_clicked)
        grid.addWidget(self.swipe_left_button)

        self.swipe_right_button = QPushButton(self)
        self.swipe_right_button.setText("swipe_right")
        self.swipe_right_button.clicked.connect(self.swipe_right_button_clicked)
        grid.addWidget(self.swipe_right_button)

        self.swipe_up_button = QPushButton(self)
        self.swipe_up_button.setText("swipe_up")
        self.swipe_up_button.clicked.connect(self.swipe_up_button_clicked)
        grid.addWidget(self.swipe_up_button)

        self.swipe_down_button = QPushButton(self)
        self.swipe_down_button.setText("swipe_down")
        self.swipe_down_button.clicked.connect(self.swipe_down_button_clicked)
        grid.addWidget(self.swipe_down_button)

        self.clockwise_button = QPushButton(self)
        self.clockwise_button.setText("clockwise")
        self.clockwise_button.clicked.connect(self.clockwise_button_clicked)
        grid.addWidget(self.clockwise_button)

        self.counterclockwise_button = QPushButton(self)
        self.counterclockwise_button.setText("counterclockwise")
        self.counterclockwise_button.clicked.connect(self.counterclockwise_button_clicked)
        grid.addWidget(self.counterclockwise_button)

        self.tap_button = QPushButton(self)
        self.tap_button.setText("tap")
        self.tap_button.clicked.connect(self.tap_button_clicked)
        grid.addWidget(self.tap_button)

        self.double_tap_button = QPushButton(self)
        self.double_tap_button.setText("double_tap")
        self.double_tap_button.clicked.connect(self.double_tap_button_clicked)
        grid.addWidget(self.double_tap_button)

        self.zoom_in_button = QPushButton(self)
        self.zoom_in_button.setText("zoom_in")
        self.zoom_in_button.clicked.connect(self.zoom_in_button_clicked)
        grid.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton(self)
        self.zoom_out_button.setText("zoom_out")
        self.zoom_out_button.clicked.connect(self.zoom_out_button_clicked)
        grid.addWidget(self.zoom_out_button)

    def closeEvent(self, event):
        event.accept()

    def view(self, gesture):

        # Select frequency and duration of beep
        frequency = 500  # Set Frequency To 2500 Hertz
        duration = 500  # Set Duration To 1000 ms == 1 second
        winsound.Beep(frequency, duration)

        self.count += 1
        print("starting ", self.count)

        # make sure the 'COM#' is set according the Windows Device Manager
        ser = serial.Serial('COM7', 19200, timeout=1)
        reader = ReadLine(ser)
        time.sleep(2)

        # Sampling the data
        self.data = []
        if gesture == "control":
            num_readings = 1000
        else:
            num_readings = 500
        for i in range(num_readings):
            line = reader.readline()  # read a byte string
            if line:
                string = line.decode().strip("\n")  # convert the byte string to a unicode string
                t = list(map(int, string.split("  ")))
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

        with open(f"{path}/candidate_{self.candidate_number}.pickle", "ab+") as file:
            pickle.dump(np.array(self.data), file)

        print("done ", self.count)


def window():
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())

window()