#include <Arduino.h>
#include "diode_calibration.h"

LightIntensityRegulator* regulator;

const int BUFFER_SIZE = 6;
char buffer[BUFFER_SIZE];
uint32_t measure_amount;

// Serial control bits
const uint16_t MEAS_START = 0xAB;
const uint16_t REDO_CALIB = 0xAC;

// Onboard LED to red
void setLedRed() {
  digitalWrite(LEDR, LOW);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, HIGH);
}

// Onboard LED to green
void setLedGreen() {
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, LOW);
  digitalWrite(LEDB, HIGH);
}

void setLedBlue() {
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, LOW);
}


void printRegulatorValue() {
  Serial.println(regulator->get_resistance());
}

void printValues() {
  int r0 = analogRead(A0);
  int r1 = analogRead(A1);
  int r2 = analogRead(A2);

  Serial.print(r0);
  Serial.print(", ");
  Serial.print(r1);
  Serial.print(", ");
  Serial.println(r2);
  delay(10);
}

// This function maintains a connection through serial with the Python data collection tool
void readSerial() {
  
  // Continuously try to read 2 bytes
  if (Serial.available() >= (int) sizeof(uint16_t)) {
    // Read first 2 bytes
    Serial.readBytes(buffer, sizeof(uint16_t));
    
    // Compare the first 2 bytes in the buffer to 0xAB (the measurement start bits) so that we initiate the measurement
    if (memcmp(&buffer, &MEAS_START, sizeof(uint16_t)) == 0 && Serial.available() >= (int) sizeof(uint32_t)) {
      // If we detected a measurement command, read the remaining uint32 so that we know how many measurements to perform
      Serial.readBytes(&buffer[2], sizeof(uint32_t));
      memcpy(&measure_amount, &buffer[2], sizeof(uint32_t));

      setLedGreen();
      // Send the regulator value once
      printRegulatorValue();
      for (uint32_t i = 0; i < measure_amount; i++) {
        // Send the photodiode values for "amount" times
        printValues();
      }
      setLedRed();
    } else if (memcmp(&buffer, &REDO_CALIB, sizeof(uint16_t)) == 0) {
      setLedBlue();
      regulator->reconfigure();
      setLedRed();
    }
  } 
}

void setup() {
  regulator = new LightIntensityRegulator();

  //in-built LED
  pinMode(LED_BUILTIN, OUTPUT);
  //Red 
  pinMode(LEDR, OUTPUT);
  //Green 
  pinMode(LEDG, OUTPUT);
  //Blue
  pinMode(LEDB, OUTPUT);

  // Turning on the Red onboard LED
  digitalWrite(LEDR, LOW);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, HIGH);
}

void loop() {
  // Comment this out to disable the bidirectional communication with the python data collection tool
  readSerial();

  // Comment this in to just print out the values like the original receiver code did
  // printValues();
}

