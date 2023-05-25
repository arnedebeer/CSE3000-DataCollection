import os
import pickle
from gesture_data import GestureData
import numpy as np

GESTURE = "digits/#1"
HAND = "right_hand"
CANDIDATE = "A3"
PATH_TO_FILE = os.getcwd() + f"/dataset/{GESTURE}/{HAND}/candidate_{CANDIDATE}.pickle"


def openFile(path):
    result = []
    with open(path, "rb") as handle:
        while True:
            try:
                b = pickle.load(handle)
                gd = GestureData.load_from_dict(b)
                result.append(gd)
            except:
                return result


if __name__ == "__main__":
    result = openFile(PATH_TO_FILE)
    print(f"file: `{PATH_TO_FILE}`\nnumber of samples: {len(result)}")
    for gd in result:
        gd.plot()
