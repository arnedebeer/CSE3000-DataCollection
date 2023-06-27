# CSE3000-DataCollection

This repository is part of the TU Delft CSE Research Project in 2023 — specifically, the project on creating TinyML-empowered Visible Light Sensing.

The repository is used to collect data to train machine learning models to recognise three types of gestures: letters (A to J), digits (0 to 9) and regular gestures such as swipe left or double tap.

The repository consists of two parts:
- An interface which sends commands over a serial interface and allows you to select the sample rate, sample time frame and the metadata for the collected data.
- A bare-bone Arduino program which waits for commands and starts sending data gathered from the photodiodes over the serial interface using the requested settings.

To use the interface one should install the required packages in ``requirements.txt`` using a package manager such as pip. To use the Arduino program one should compile the program using the ``PlatformIO`` framework and upload it to the microcontroller.
Connect the microcontroller, using a serial connection, to the device that will run the PyQt5 interface. Select the right port, configure the collection settings and click the gesture you would like to record.
