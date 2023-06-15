
from sklearn.linear_model import LinearRegression
import numpy as np


class PathPredictictor():

    model: LinearRegression = None

    def __init__(self):
        known_sensor_values = [
            [156, 113, 150], # Top left
            [150, 123, 276], # Top middle
            [249, 117, 320], # Top right
            [294, 129, 143], # Center left
            [309, 136, 274], # Center middle
            [332, 135, 333], # Center right
            [314, 165, 151], # Bottom left
            [321, 187, 263], # Bottom middle
            [333, 156, 334], # Bottom right
        ]

        known_hand_positions = [
            [0, 2], # Top left
            [1, 2], # Top middle
            [2, 2], # Top right
            [0, 1], # Center left
            [1, 1], # Center middle
            [2, 1], # Center right
            [0, 0], # Bottom left
            [1, 0], # Bottom middle
            [2, 0], # Bottom right
        ]



        # Prepare your data
        # X represents the sensor values, and y represents the corresponding hand position coordinates
        X = np.array([[sensor_value1, sensor_value2, sensor_value3] for sensor_value1, sensor_value2, sensor_value3 in known_sensor_values])
        y = np.array([[x_coordinate, y_coordinate] for x_coordinate, y_coordinate in known_hand_positions])

        # Create a linear regression model
        model = LinearRegression()

        # Train the model
        model.fit(X, y)

        self.model = model

    def predict(self, sensor_values: list) -> list:
        # Predict the hand position coordinates from the sensor values
        return self.model.predict(sensor_values)