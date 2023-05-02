import glob
import pickle
import os.path
from enum import Enum
from itertools import takewhile
from os.path import split, dirname
from rich.progress import track
from statistics import mean
from typing import Tuple
import numpy as np
import subprocess


BOUNDARY_TOLERANCE = 0.05 # Controls the percentage from constant values that readings can deviate before being discarded
CLOSE_TO_ONE_EPSILON = 1e-3
DIST_FROM_MIN_TO_MAX = 0.75


class SelectionStrategy(Enum):
    MIN = 0
    MAX = 1
    MEAN = 2
    MIN_MAX_SKEW = 3


class FormatData():
    """Class used for passing the raw data through to the processing pipeline.

    The data is first formatted in the format the pipeline expects and saved under a "preprocessed" directoru.
    This formatted data is then passed through the pipeline and saved under a "post_process" directory.
    Finally, this post processed data is converted back to the original format and saved under a "reformatted" directory.
    """

    def __init__(self):
        self.base_paths = []
        self.path_to_data = "./src/data_collection/data"
        self.pass_through_pipeline()
        self.convert_processed_files()


    def _generate_threshold(self, data: np.ndarray, start_avg: np.float32, end_avg: np.float32,
                            strategy: SelectionStrategy = SelectionStrategy.MEAN) -> float:
        if strategy is SelectionStrategy.MIN:
            return min(start_avg, end_avg)
        elif strategy is SelectionStrategy.MAX:
            return max(start_avg, end_avg)
        elif strategy is SelectionStrategy.MEAN:
            return mean([start_avg, end_avg])
        elif strategy is SelectionStrategy.MIN_MAX_SKEW:
            min_val = np.min(data)
            max_val = np.max(data)
            return min_val + ((max_val - min_val) * DIST_FROM_MIN_TO_MAX)


    def _compute_thresholds_from_data(self, data: np.ndarray,
                                      strategy: SelectionStrategy = SelectionStrategy.MEAN) -> Tuple[np.float32, np.float32, np.float32]:
        thresholds = np.zeros(3, dtype=np.float32)
        first_samples = data[0]
        last_samples = data[-1]

        for photodiode in range(3):
            # Take all values within a percentage of the very first and very last readings
            start_const_vals = takewhile(
                lambda sample: abs((sample - first_samples[photodiode]) / 100) < BOUNDARY_TOLERANCE,
                data[:, photodiode])
            end_const_vals = takewhile(
                lambda sample: abs((sample - last_samples[photodiode]) / 100) < BOUNDARY_TOLERANCE,
                np.flip(data[:, photodiode]))

            # Compute average of constant values and use chosen strategy to generate threshold
            start_const_mean = mean(list(start_const_vals))
            end_const_mean = mean(list(end_const_vals))
            thresholds[photodiode] = self._generate_threshold(data, start_const_mean, end_const_mean, strategy)
        
        return thresholds[0], thresholds[1], thresholds[2]


    def _detect_all_ones(self, data: np.ndarray) -> bool:
        ones = np.ones(data.shape)
        close_to_one = np.isclose(data, ones, atol=CLOSE_TO_ONE_EPSILON)
        return np.all(close_to_one)


    def convert_processed_files(self):
        """
        This reads through the data that was passed through the pipeline and converts it back to the original format
        """
        self._all_zero_paths = []

        # Get a list of all the paths
        self.base_paths = []
        for directory in glob.iglob(f"./post_process/{self.path_to_data}" + '**/**/**/candidate*', recursive=True):
            self.base_paths.append(directory)

        for path in track(self.base_paths, description="Converting processed files..."):
            head, tail = os.path.split(path)
            pre_path = "/reformatted"
            filenames = os.listdir(path)
            data_to_pickle = []

            # Get the data from the files
            for filename in filenames:
                data = np.loadtxt(path + "/" + filename)
                data_to_pickle.append(data)
                
                # Check if data is all ones
                if self._detect_all_ones(np.array(data)):
                    self._all_zero_paths.append(path + "/" + filename)

            new_path = os.getcwd() + f"{pre_path}/{head}"
            if (not os.path.exists(new_path)):
                os.makedirs(new_path)

            # Save the data back into pickled files
            with open(f"{new_path}/{tail}.pickle", "wb+") as f:
                for data in data_to_pickle:
                    pickle.dump(data, f)

        # Report files that are all ones
        print("===== ALL ONES REPORT =====")
        for faulty_file in self._all_zero_paths:
            print(f"> {faulty_file}")


    def pass_through_pipeline(self):
        """
        This reads through the data that needs to be passed through the pipeline and converts a copy of it to the format
        that the pipeline expects then passes this new data through the pipeline
        """
        # Get all the paths for data we want to pass through to pipeline
        self.base_paths = []
        for directory in glob.iglob(self.path_to_data + '**/**/*_hand', recursive=True):
            self.base_paths.append(directory)

        # Path to prepend
        pre_dir = "/preprocessed"

        # Go through every path
        for base_path in track(self.base_paths, description="Passing raw data through pipeline..."):
            # Get all files in the path
            for filename in glob.iglob(f'{base_path}/*.pickle', recursive=True):
                # Extract all the data from the file
                with open(filename, 'rb') as f:
                    self.unpickled = []
                    while True:
                        try:
                            self.unpickled.append(pickle.load(f))
                        except EOFError:
                            break

                # Get the candidate number from the path
                candidate = split(filename)[1].replace(".pickle", "")
                path_dir = dirname(filename)

                # Get the threshold values from the control path
                # medians = self.get_baselines(candidate)

                # Create a new path where the reformatted unprocessed data will be saved
                new_path = pre_dir+path_dir+"/"+candidate
                full_path = os.getcwd() + "/" + new_path

                # Create a new path where the processed data will be saved
                post_process_path = "./post_process"+path_dir+"/"+candidate

                if (not os.path.exists(full_path)):
                    os.makedirs(full_path)

                if (not os.path.exists(post_process_path)):
                    os.makedirs(post_process_path)

                for i, iteration in enumerate(self.unpickled):
                    thresholds = self._compute_thresholds_from_data(iteration, SelectionStrategy.MEAN)

                    # Save the pickled data in the format that the pipeline expects
                    with open(f"{full_path}/iteration_{i}.txt", 'w') as f:
                        f.write(str(len(iteration)))
                        f.write("\n")
                        f.write(f"{int(thresholds[0])} {int(thresholds[1])} {int(thresholds[2])}")
                        for row in iteration:
                            f.write("\n")
                            f.write(f"{row[0]} {row[1]} {row[2]}")

                    # Run the pipeline on the reformatted unprocessed data that gets saved in the post_process path
                    subprocess.run(
                        ["../receiver-desktop/main", f"../data_collection{new_path}/iteration_{i}.txt", f"{post_process_path}/iteration_{i}.txt"],
                        capture_output=True)


    def get_baselines(self, candidate):
        with open(f"{self.path_to_data}/control/{candidate}.pickle", 'rb') as f:
            data = pickle.load(f)
            medians = np.median(data, 0)
        return medians


if __name__ == '__main__':
    FormatData()
    