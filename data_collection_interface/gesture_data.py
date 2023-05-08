# Following lines are to avoid cyclic dependencies in type checking.
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collector import Collector

import matplotlib.pyplot as plotter
import os


class GestureData:

    def __init__(self, resistance: int, sampling_rate: int, duration: float, data = [], 
                    candidate: str = "Unknown Candidate", target_gesture: str = "Unknown Gesture") -> None:
        self.candidate = candidate
        self.target_gesture = target_gesture
        self.resistance = resistance
        self.sampling_rate = sampling_rate
        self.duration = duration
        self.samples = int(duration * sampling_rate)
        self.data = data

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


    # Plots the data contained in the GestureData on a graph.
    def plot(self, show=True, candidate = None, gesture = None) -> None:
        # Set metadata of the plot.
        if (candidate != None):
            self.candidate = candidate
        if (gesture != None):
            self.target_gesture = gesture

        # Create the plot, together with a section for the metadata.
        fig, plt = plotter.subplots(1)
        fig.subplots_adjust(bottom=0.3)

        # Plot the data.
        plt.plot(self.data)

        # Set the labels of the axes.
        plt.set_xlabel("Samples")
        plt.set_ylabel("Photodiode reading")

        # Set the metadata
        # fig.text(0.1,0.05,'Sampling Rate: ' + str(self.sampling_rate) + 'Hz')
        # fig.text(0.38,0.05,'Time: ' + str(self.duration) + 's')
        # fig.text(0.5,0.05,'Resistance: ' + str(self.resistance / 1000) + 'kOhm')
        fig.text(0.1,0.15,'Sampling Rate: ' + str(self.sampling_rate) + 'Hz')
        fig.text(0.1,0.10,'Time: ' + str(self.duration) + 's')
        fig.text(0.1,0.05,'Resistance: ' + str(self.resistance / 1000) + 'kOhm')

        # Set the title of the plot.
        title = self.target_gesture + " by " + self.candidate
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