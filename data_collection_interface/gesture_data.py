# Created by Winstijn Smit on 9 May 2023.

# Following lines are to avoid cyclic dependencies in type checking.
from __future__ import annotations
from typing import TYPE_CHECKING

from path_predictor import PathPredictictor
if TYPE_CHECKING:
    from collector import Collector

from PyQt5.QtWidgets import QMessageBox

import pickle
import numpy as np
import matplotlib.pyplot as plotter
import matplotlib.widgets as widgets
import os
import time

COLLECTION_PATH = "./dataset"


class GestureData:

    data: list

    # Create static method that sets a gesture from a dictionary.
    @staticmethod
    def load_from_dict(obj: dict):
        gesture_data = GestureData(0, 0, 0)
        gesture_data.set(obj)
        return gesture_data
        
    # Sets values from a dictionary.
    def set(self, obj: dict):
        valid_keys = ["resistance", "sample_rate", "duration", "samples", "data", "candidate", "hand", "gesture_type", "target_gesture", "timestamp"]
        for key in obj:
            if key not in valid_keys:
                raise Exception("Invalid key '" + key + "'")
            setattr(self, key, obj[key])


    def __init__(self, resistance: int, sample_rate: int, duration: float) -> None:
        self.resistance = resistance
        self.sample_rate = sample_rate
        self.duration = duration
        self.samples = int(duration * sample_rate)
        self.set_metadata() # Just initialize the metadata values.
        self.timestamp = time.time()
        self.data = [] # Initialize the data list to an empty array.

    def set_metadata(self, candidate: str = "Unknown Canidate", hand: str = "unknown",
                     gesture_type="unknown", target_gesture="unknown") -> None:
        self.candidate = candidate
        self.hand = hand
        self.gesture_type = gesture_type
        self.target_gesture = target_gesture

    # Removes this GestureData from the file it is stored in.
    # This assumes it is saved at the default location.
    # Might need refactoring for when this is not the case.
    def remove_from_dataset(self) -> None:
        path = self.get_pickle_path()
        remove_entry_at(path, self.timestamp)

    # Add a sample to the data.
    def add_sample(self, r0, r1, r2) -> None:
        self.data.append([int(r0), int(r1), int(r2)])

    # Uses a collctor to read all the samples retrieved from the serial port.
    def collect(self, collector: Collector, log=False) -> None:
        # Get all measurements samples from the serial port.
        for i in range(self.samples):
            # Read a line from the serial port.
            # Get the binary result.
            r0 = collector.readuint16()
            r1 = collector.readuint16()
            r2 = collector.readuint16()
            self.add_sample(r0, r1, r2)

            if log:
                print("[Measurement " + str(i) + "] " + str(r0) + ", " + str(r1) + ", " + str(r2))

    def get_directory_path(self, folder=COLLECTION_PATH) -> str:
        return os.path.join(folder, self.gesture_type, self.target_gesture, self.hand)

    # Getter for candidate name without spaces
    def get_formatted_candidate(self) -> str:
        return self.candidate.lower().replace(" ", "_")

    def get_pickle_path(self, folder=COLLECTION_PATH):
        # Create the path to the file
        candidate = self.get_formatted_candidate()
        directory = self.get_directory_path(folder)
        return os.path.join(directory, "candidate_" + candidate + ".pickle")

    def save_to_file(self, folder=COLLECTION_PATH, path=None) -> None:
        # Create the directory if it does not exist.
        data_dict = {
            "timestamp": self.timestamp,
            "candidate": self.candidate,
            "hand": self.hand,
            "gesture_type": self.gesture_type,
            "target_gesture": self.target_gesture,
            "resistance": self.resistance,
            "sample_rate": self.sample_rate,
            "duration": self.duration,
            "samples": self.samples,
            "data": np.array(self.data)
        }

        if path == None:
            path = self.get_pickle_path(folder)

        create_directories(path) # Create the directories if they do not exist.
        print("Saving gesture data to file at: " + str(path))

        with open(path, "ab+") as file:
            pickle.dump(data_dict, file)

    # Plots the data contained in the GestureData on a graph.
    def plot(self, show=True, candidate = None, target_gesture = None) -> None:
        # Set metadata of the plot.
        if (candidate == None):
            candidate = self.candidate
        if (target_gesture == None):
            target_gesture = self.target_gesture

        # Create the plot, together with a section for the metadata.
        fig, plt = plotter.subplots(1)
        fig.subplots_adjust(bottom=0.3)

        # Plot the data.

        # x_values = []
        # y_values = []

        # for i in range(0, len(self.data)):
        #     x_values.append(self.data[i][1] * 0.2 + self.data[i][2] * 0.8)
        #     y_values.append(self.data[i][0] * 0.5)

        # x_values = np.convolve(np.pad(x_values, (5//2, 5//2), mode='edge'), np.ones(5) / 5, mode='valid')
        # y_values = np.convolve(np.pad(y_values, (5//2, 5//2), mode='edge'), np.ones(5) / 5, mode='valid')

        pp = PathPredictictor()
        path = pp.predict(self.data).transpose()
        plt.plot(path[0], path[1], color="red")

        # Set the labels of the axes.
        plt.set_xlabel("Samples")
        plt.set_ylabel("Photodiode reading")

        # Set the metadata of the plot.
        fig.text(0.1,0.15,'Sampling Rate: ' + str(self.sample_rate) + 'Hz')
        fig.text(0.1,0.10,'Time: ' + str(self.duration) + 's')
        fig.text(0.1,0.05,'Resistance: ' + str(self.resistance / 1000) + 'kOhm')

        # Set the title of the plot.
        title = target_gesture + " by " + candidate
        plt.set_title(title) 

        print(self.data[len(self.data) - 1])
        print(self.data)
        
        # If "d" is pressed, prompt the user to remove the gesture from the dataset.
        def on_key(event):  
            if event.key == "d":
                # Prompt the user to confirm the removal using Qt   
                result = prompt_remove_dataset()
                if result == QMessageBox.Ok:
                    print("Removing gesture from dataset...")
                    remove_entry_at(self.get_pickle_path(), self.timestamp)
                    plotter.close()
                else:
                    print("Canceling gesture removal...")

        fig.canvas.mpl_connect('key_press_event', on_key)


        # Save location of the image.
        path = "plots/" + title.lower().replace(" ", "_") + ".png"
        create_directories(path)
        plotter.savefig(path)

        if (show):
            plotter.show()


def prompt_remove_dataset():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText("Are you sure you want to remove this gesture from the dataset?")
    msg.setWindowTitle("Remove gesture from dataset")
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.setEscapeButton(QMessageBox.Cancel)
    return msg.exec_()

# Remove a dataset entry at a certain path with a certain timestamp.
# Note that this is not the best way to do this, but it works for now.
def remove_entry_at(path: str, timestamp: float):
    if os.path.exists(path):
        data = read_pickle(path)
        # Check if the data is in the list.
        # Map the data so we only have the timestamp
        data_time = list(map(lambda x: x.timestamp, data))

        # Use the timestamp to find the index.
        index = data_time.index(timestamp) # Use the timestamp to find the index.
        if (index != -1):
            print("=== Removed one entry from dataset at '" + path + "'")
            # Remove the index from the list.
            data = data[:index] + data[index+1:]
            
            os.remove(path)  # remove the original file first
            print("Resaving the left over data:")
            write_pickle(path, data) # Rewrite the file again.

def create_directories(path: str) -> None:
    # Create directory structure if it doesn't exist yet
    path = os.path.dirname(path)
    if not os.path.exists(path):
        os.makedirs(path)

def read_pickle(path: str) -> list[GestureData]:
    # Read the pickle file.
    data = []
    with open(path, "rb") as file:
        # As many times as possible try to read a pickle object.
        try:
            while True: 
                gd_dict = pickle.load(file)
                data.append(GestureData.load_from_dict(gd_dict))
        except EOFError:
            pass
    return data

def write_pickle(path: str, data: list[GestureData]) -> None:
    for gd in data:
        gd.save_to_file(path=path) # Save all the gesture data to a file.
