#include <Arduino.h>
#include "diode_calibration.hpp"
#include "leds.hpp"
#include "map"

// Uncomment this to get binary responses for photodiode values.
#define BINARY_RESPONE 0x00

LightIntensityRegulator* regulator;

// Sample rate in hertz
// Can be changed over the serial interface.
// Maximum is around 1200 Hz.
uint16_t SAMPLE_RATE = 100; 
uint32_t SAMPLE_RATE_DELAY_MICROS = 1000000 / SAMPLE_RATE;

// Helper funtion to read and return a value from the serial.
// Wrap it into its own type (template)
template <typename T>
void getValueFromSerial(T *buffer) {

  // Wait until the right amount of bytes are available.
  // while (Serial.available() < (int) sizeof(T));

  // Read the amount of bytes that we need.
  // And store them in the buffer.
  Serial.readBytes((char*) buffer, sizeof(T));
}

// Helper function to read the photodiodes at a given sample rate.
// Returns the results over the serial interface.
void readPhotodiodes() {
  const unsigned long start = micros();

  uint16_t r0 = (uint16_t) analogRead(A0);
  uint16_t r1 = (uint16_t) analogRead(A3);
  uint16_t r2 = (uint16_t) analogRead(A4);

  #ifdef BINARY_RESPONE
    Serial.write((char*) &r0, sizeof(uint16_t));
    Serial.write((char*) &r1, sizeof(uint16_t));
    Serial.write((char*) &r2, sizeof(uint16_t));
  #else
    Serial.print(r0);
    Serial.print(", ");
    Serial.print(r1);
    Serial.print(", ");
    Serial.println(r2);
  #endif

  // Delay only if we have time left.
  const unsigned long diff = micros() - start + 4; // Add offset to compensate if statement
  if (diff < SAMPLE_RATE_DELAY_MICROS) {
      delayMicroseconds(SAMPLE_RATE_DELAY_MICROS - diff);
  }
}

// Command start of a measurement.
// Expects 4 bytes (uint32_t) that represent the amount of samples to be returned
// Uses the sample rate that is currently set.
const char MEASUREMENT_START = 0xAB;
void measurementCommand() {
    setLedGreen();

    // Collect the amount of samples to be taken.
    uint32_t samples = 0;
    getValueFromSerial(&samples);

    // Read the photodiodes for the amount of samples.
    for (uint32_t i = 0; i < samples; i++) {
      readPhotodiodes();
    }
  
    Serial.println("Finished measuring command.");
}

// Command recalibration of resistor values.
const char RECALIBRATE = 0xAC;
void recalibrateCommand () {
    setLedOrange();
    regulator->reconfigure();

    // Return the resistance that has been set.
    Serial.println(regulator->get_resistance()); 
}


// Set the sample rate. (in Hertz)
// Expects 2 bytes (uint16_t) that represent the sample rate.
const char SET_SAMPLE_RATE = 0xAD;
void setSampleRateCommand() {
  setLedBlue();

  // Wait for sample rate to be available.
  uint16_t sample_rate = 0;
  getValueFromSerial(&sample_rate);

  // Set the sample rate.
  SAMPLE_RATE = sample_rate;
  SAMPLE_RATE_DELAY_MICROS = 1000000 / SAMPLE_RATE;

  Serial.print("Sample rate set to: ");
  Serial.print(sample_rate);
  Serial.println(" Hz");
}

// Make a map that contains the different commands that we can receive from the serial.
// and the functions that we should call when we receive them.
typedef void (*command_function)();
typedef std::map<char, command_function> command_map;
command_map commands = 
{
  {MEASUREMENT_START, measurementCommand},
  {RECALIBRATE, recalibrateCommand},
  {SET_SAMPLE_RATE, setSampleRateCommand}
};

// Function that processes a command that we received from the serial.
// If the command is not in the map, we print an error message.
void processCommand(char command) {
  // setLedPurple();
  // delay(1000);

  // Get the function
  command_function function = commands[command];

  // if the function is not null, call it.
  if (function != NULL) {
    function();
    return;
  }
  
  // If reaching here we received an unknown command  
  Serial.println("Received unknown command from serial.");
}

// Function that reads the serial input and interprets it as a command.
void waitForCommand() {

  // Set led to white to indicate that we are waiting for a command.
  setLedWhite(); 

  while (Serial.available() >= 1) {
      // Read the command from the serial.
      char command = Serial.read();
      processCommand(command);
  }
}


void setup() {
  regulator = new LightIntensityRegulator();

  // Initialize LED
  setupLeds();
}

// Loop that runs continuously.
// It essentially waits for a command from the serial and processes it.
void loop() {
  waitForCommand();
}
