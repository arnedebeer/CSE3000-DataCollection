# New version of the window.

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QPushButton, QComboBox, QLineEdit, QLabel, QMessageBox
import sys
from util import serial_ports, auto_select_serial_port
from collector import Collector
import time

DEFAULT_CANDIDATE = "default"

DATASET_FOLDER = "data/"

START_DELAY = 500 # Delay before measurment starts in ms.

# Whole gesture selection UI is created from these constants.
GESTURE_TYPES = ["gestures", "digits", "letters"]
GESTURES = { 
    "gestures":  ["swipe_left", "swipe_right", "swipe_up", "swipe_down", "clockwise", "counter_clockwise", "tap", "double_tap", "zoom_in", "zoom_out"],
    "digits": ["#" + str(i) for i in range(10)], # #1, #2, #3, etc.
    "letters": [("char_" + chr(i)) for i in range(ord('A'), ord('J')+1)]
}
DEFAULT_GESTURE_TYPE = "gestures" # Easy for testing.

# The default sample rate and duration for each gesture type.\
# Make sure these values are also defined in the arrays below.
DEFAULTS_PER_GESTURE_TYPE = {
    "gestures": {
        "sample_rate": 100,
        "sample_duration": 1000,
    },
    "digits": {
        "sample_rate": 1000,
        "sample_duration": 1500,
    },
    "letters": {
        "sample_rate": 100,
        "sample_duration": 4000,
    },
}

SAMPLE_RATES = [100, 250, 500, 750, 1000, 1250, 1500]
SAMPLE_DURATIONS =  [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]

class CollectionWindow(QMainWindow):

    sample_rate: int
    serial_port: str
    candidate_identifier: str
    chosen_hand: str # Change this to an enum later.
    gesture_type: str
    resistance: int

    def __init__(self):
        super(CollectionWindow, self).__init__()

        self.available_ports = serial_ports()
        self.sample_rate = 100

        # Select the default serial port.
        self.serial_port = auto_select_serial_port()

        self.candidate_identifier = DEFAULT_CANDIDATE
        self.chosen_hand = "right"
        self.resistance = None # Has not been calibrated yet.

        # Set the default gesture types and the defaults related to them.
        self.gesture_type = DEFAULT_GESTURE_TYPE

        # Initialize the window.
        self.initializeUI()

        # Set the default sample settings in the UI.
        self.set_default_sample_settings()



    def recalibrate(self):
        self.resistance = self.collector().recalibrate()

    def collector(self):
        return Collector(self.serial_port)
    
    def measure(self, gesture, save=True):
        if (self.resistance is None):
            self.recalibrate() # Only recalibrate if we haven't already.

        # Sleep for a bit before starting the measurement.
        time.sleep(START_DELAY / 1000)

        print("\n========== Start of measurement ===========")
        print("[UI] Collecting data for candidate '{}' with '{}' for gesture '{}' ({}) at sample rate '{} Hz' with '{} kOhm' resistance for '{} ms'".format
              (self.candidate_identifier, self.chosen_hand, gesture, self.gesture_type, self.sample_rate, self.resistance / 1000, self.sample_duration))
        collector = self.collector()
        collector.resistance = self.resistance # Set the resistance, to avoid recalibrating.

        data = collector.measure(duration=self.sample_duration / 1000, sample_rate=self.sample_rate)
        print(len(data.data))
        print("========== End of measurement ===========\n")

        # Set metadata for the data.
        data.set_metadata(candidate=self.candidate_identifier, 
                          hand=self.chosen_hand, 
                          gesture_type=self.gesture_type, 
                          target_gesture=gesture)

        if save:
            data.save_to_file() # Save the data to a file.
        data.plot() # Plot the data.

    def initializeUI(self):
        self.setWindowTitle("Data Collection Interface")
        # self.setGeometry(300, 300, 800, 600)

        # Connecting quit function
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)
        
        # QT display
        w = QtWidgets.QWidget()
        self.setCentralWidget(w)
        # self.setGeometry(200, 200, 300, 300)

        self._general_grid = QtWidgets.QGridLayout(w)

        # Create the different UI elements.
        self.create_port_dropdown()
        self.create_calibration_button()
        self.create_hand_button()
        self.create_input("Candidate name:", "candidate_identifier")
        self.create_gesture_type_dropdown()
        self.create_sample_rate_dropdown()
        self.create_sample_duration_dropdown()
        self.create_test_button()
        self.create_gesture_buttons()

    def create_dropdown(self, label: str, options: list, field: str, on_change=None) -> QComboBox :
        # Default dropdown changed function.
        def dropdown_changed(changedToIndex):
            setattr(self, field, options[changedToIndex])
            if on_change is not None:
                on_change(changedToIndex)

        # Create the dropdown.
        dropdown = QComboBox()
        dropdown.addItems(options)
        dropdown.currentIndexChanged.connect(dropdown_changed)

        # Set the initial value of the dropdown to the value of the field
        if (hasattr(self, field)): # Only if the field already exists.
            val = getattr(self, field) # Get the value of the field.
            default_index = options.index(val) if val in options else 0 # Look for the index of the value in the options.
            dropdown.setCurrentIndex(default_index) # Set the dropdown to the index.

        # Add to the general grid.
        self._general_grid.addWidget(QLabel(label))
        self._general_grid.addWidget(dropdown)

        return dropdown

    def create_port_dropdown(self):
        dropdown = self.create_dropdown("Serial Port:", self.available_ports, "serial_port")

    def create_sample_rate_dropdown(self):
        def change_sample_rate(index):
            self.sample_rate = SAMPLE_RATES[index]

        self.sample_rate_dropdown = self.create_dropdown("Sample Rate: (frequency)", list(map(lambda x: str(x) + " Hz", SAMPLE_RATES)), "sample_rate", change_sample_rate)

    def create_sample_duration_dropdown(self):
        def change_sample_duration(index):
            self.sample_duration = SAMPLE_DURATIONS[index]

        self.sample_duration_dropdown = self.create_dropdown("Sample Duration: (millisconds)", list(map(lambda x: str(x) + " ms", SAMPLE_DURATIONS)), "sample_duration", change_sample_duration)

    def set_default_sample_settings(self):
        # Set the default sample rate and duration for the current gesture type.
        self.sample_rate = self.get_default("sample_rate")
        self.sample_duration = self.get_default("sample_duration")

        # Set the dropdowns to the right values if they exist.
        if hasattr(self, "sample_rate_dropdown"):
            self.sample_rate_dropdown.setCurrentIndex(SAMPLE_RATES.index(self.sample_rate))
        if hasattr(self, "sample_duration_dropdown"):
            self.sample_duration_dropdown.setCurrentIndex(SAMPLE_DURATIONS.index(self.sample_duration))

    def create_gesture_type_dropdown(self):
        def show_gesture_buttons(index):
            self.show_gesture_buttons(index)
            self.set_default_sample_settings()

        self.create_dropdown(label="Gesture Type:", options=GESTURE_TYPES, field="gesture_type", on_change=show_gesture_buttons)

    def create_input(self, label: str, field: str):
        
        def input_changed(changedTo):
            # Get the attribute name from the field.
            setattr(self, field, changedTo)

        textfield = QLineEdit()
        attr = getattr(self, field)
        textfield.setText(attr)
        textfield.textChanged.connect(input_changed)

        # Add to the general grid.
        self._general_grid.addWidget(QLabel(label))
        self._general_grid.addWidget(textfield)
    

    def create_hand_button(self):
        chosen_hand_button = QPushButton("Right Hand", self)
        self.chosen_hand = "right_hand"

        def chosen_hand_button_clicked():
            if chosen_hand_button.isChecked():
               chosen_hand_button.setStyleSheet("background-color : purple")
               chosen_hand_button.setText("Left Hand")
               self.chosen_hand = "left_hand"
            else:
               chosen_hand_button.setStyleSheet("background-color : orange")
               chosen_hand_button.setText("Right Hand")
               self.chosen_hand = "right_hand"

        chosen_hand_button.setCheckable(True)
        chosen_hand_button.clicked.connect(chosen_hand_button_clicked)
        chosen_hand_button.setStyleSheet("background-color : orange")
        
        self._general_grid.addWidget(chosen_hand_button)

    def show_gesture_buttons(self, index):
        if not hasattr(self, "gesture_button_frames"):
            return # Gesture buttons not initialized yet, do nothing.
        
        for frame in self.gesture_button_frames:
            frame.hide()
        self.active_frame = self.gesture_button_frames[index]
        self.active_frame.show()

    def create_gesture_buttons(self):
        # Create all frames for all the gesture types.
        self.gesture_button_frames = []
        for gesture in GESTURES.values():
            frame = self.generate_frame(gesture)
            self._general_grid.addWidget(frame)
            self.gesture_button_frames.append(frame)

        # Show the gesture button frame for the current gesture type.
        self.show_gesture_buttons(GESTURE_TYPES.index(self.gesture_type))

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

    def create_calibration_button(self):
        calibration_button = QPushButton("Recalibrate Sensitivty", self)
        calibration_button.clicked.connect(self.recalibrate)
        calibration_button.setStyleSheet("background-color : grey; color: white")

        # Add to the general grid.
        self._general_grid.addWidget(calibration_button)

    def create_test_button(self):
        test_button = QPushButton("Self-test", self)
        test_button.clicked.connect(lambda: self.measure("test", False))
        test_button.setStyleSheet("background-color: purple; color: white")

        # Add to the general grid.
        self._general_grid.addWidget(test_button)

    def data_button_clicked(self):
        if self.serial_port is None:
            msg = QMessageBox()
            msg.setText("No serial port selected for serial connection...")
            msg.exec()
        else:
            print("Data button clicked")
            # print(self.sender().text()) 
            self.measure(self.sender().text())

    def get_default(self, field):
        defaults = DEFAULTS_PER_GESTURE_TYPE[self.gesture_type]
        if defaults is None or field not in defaults:
            raise Exception("No default value for field: " + field)
    
        return defaults[field]
        

    # Allow closing the window.
    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CollectionWindow()
    window.show()
    sys.exit(app.exec_())


# Catch the KeyboardInterrupt exception.

