# Following lines are to avoid cyclic dependencies in type checking.
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collector import Collector

import pickle
import matplotlib.pyplot as plotter
import os

COLLECTION_PATH = "./dataset"

class GestureData:

    def __init__(self, resistance: int, sample_rate: int, duration: float, data = []) -> None:
        self.resistance = resistance
        self.sample_rate = sample_rate
        self.duration = duration
        self.samples = int(duration * sample_rate)
        self.set_metadata() # Just initialize the metadata values.
        self.data = data

    def set_metadata(self, candidate: str = "Unknown Canidate", hand: str = "unknown",
                     gesture_type="unknown", target_gesture="unknown") -> None:
        self.candidate = candidate
        self.hand = hand
        self.gesture_type = gesture_type
        self.target_gesture = target_gesture


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

    def save_to_file(self, folder=COLLECTION_PATH) -> None:
        # Create the directory if it does not exist.
        data_dict = {
            "candidate": self.candidate,
            "hand": self.hand,
            "gesture_type": self.gesture_type,
            "target_gesture": self.target_gesture,
            "resistance": self.resistance,
            "sample_rate": self.sample_rate,
            "duration": self.duration,
            "samples": self.samples,
        }

        # Create the path to the file
        candidate = self.get_formatted_candidate()
        directory = self.get_directory_path(folder)
        path = os.path.join(directory, "candidate_" + candidate + ".pickle")
        
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
        plt.plot(self.data)

        # Set the labels of the axes.
        plt.set_xlabel("Samples")
        plt.set_ylabel("Photodiode reading")

        # Set the metadata
        # fig.text(0.1,0.05,'Sampling Rate: ' + str(self.sample_rate) + 'Hz')
        # fig.text(0.38,0.05,'Time: ' + str(self.duration) + 's')
        # fig.text(0.5,0.05,'Resistance: ' + str(self.resistance / 1000) + 'kOhm')
        fig.text(0.1,0.15,'Sampling Rate: ' + str(self.sample_rate) + 'Hz')
        fig.text(0.1,0.10,'Time: ' + str(self.duration) + 's')
        fig.text(0.1,0.05,'Resistance: ' + str(self.resistance / 1000) + 'kOhm')

        # Set the title of the plot.
        title = target_gesture + " by " + candidate
        plt.set_title(title) 

        # Save location of the image.
        path = "gestures/" + title.lower().replace(" ", "_") + ".png"
        create_directories(path)
        plotter.savefig(path)

        if (show):
            plotter.show()

def create_directories(path: str) -> None:
    # Create directory structure if it doesn't exist yet
    path = os.path.dirname(path)
    if not os.path.exists(path):
        os.makedirs(path)