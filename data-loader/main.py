# Written by Sem van den Broek on 03-05-2023

import os
import pickle
import re
import matplotlib.pyplot as plotter
from enum import Enum


class Hand(Enum):
    right = "right_hand"
    left = "left_hand"


class GestureNames(Enum):
    char_A = "char_A"
    char_B = "char_B"
    char_C = "char_C"
    char_D = "char_D"
    char_E = "char_E"
    char_F = "char_F"
    char_G = "char_G"
    char_H = "char_H"
    char_I = "char_I"
    char_J = "char_J"



class LoadGestureException(Exception):
    pass


def load_gesture_samples(gesture_name: GestureNames, hand: Hand = Hand.right):
    result = []
    base_path = f"dataset/letters/{gesture_name.value}/{hand.value}"
    folder_items = os.listdir(base_path)

    # Filter on the .pickle extension
    filtered_ext = list(filter(lambda x: re.search(r'\.pickle$', x) is not None, folder_items))

    if len(filtered_ext) == 0:
        raise LoadGestureException("No gestures found in folder: %s" % base_path)

    for item in filtered_ext:
        r_match = re.match(r'candidate_(\w+).pickle$', item)
        if r_match is None:
            raise LoadGestureException("Incorrectly formatted data file name: %s" % item)

        candidate_id = r_match.group(1)
        with open(os.path.join(base_path, item), 'rb') as f:
            while True:
                try:
                    data_contents = pickle.load(f)

                    if isinstance(data_contents, dict):
                        result.append(data_contents)
                    else:
                        # Old data loader
                        data = {
                            'data': data_contents,
                            'gesture': gesture_name.value,
                            'candidate': candidate_id
                        }
                        result.append(data)
                except EOFError:
                    break

    return result

def plot(data : dict = None) -> None:


    # Create the plot, together with a section for the metadata.
    fig, plt = plotter.subplots(1)
    fig.subplots_adjust(bottom=0.3)

    # Plot the data.
    plt.plot(data["data"])

    # Set the labels of the axes.
    plt.set_xlabel("Samples")
    plt.set_ylabel("Photodiode reading")

    # Set the metadata of the plot.
    fig.text(0.1,0.15,'Sampling Rate: ' + str(data["sample_rate"]) + 'Hz')
    fig.text(0.1,0.10,'Time: ' + str(data["duration"]) + 's')

    fig.text(0.1,0.05,'Resistance: ' + str(data["resistance"] / 1000) + 'kOhm')


    # Set the title of the plot.
    title = data["target_gesture"] + " by " + data["candidate"]

    plt.set_title(title) 
    
    plotter.show()



data :list = load_gesture_samples(GestureNames.char_A)

print(data[2])

for candidate_data in data:
    print(candidate_data)