#include <Arduino.h>
#include "diode_calibration.h"

LightIntensityRegulator* regulator;

const int BUFFER_SIZE = 6;
char buffer[BUFFER_SIZE];

// Onboard LED to green
void setLedGreen() {
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDG, LOW);
  digitalWrite(LEDB, HIGH);
}

// Onboard LED to red
void setLedRed() {
  digitalWrite(LEDR, LOW);
  digitalWrite(LEDG, HIGH);
  digitalWrite(LEDB, HIGH);
}

void printRegulatorValue() {
  Serial.println(regulator->get_resistance());
}

void printValues() {
  int r0 = analogRead(A0);
  int r1 = analogRead(A3);
  int r2 = analogRead(A4);

  Serial.print(r0);
  Serial.print(", ");
  Serial.print(r1);
  Serial.print(", ");
  Serial.println(r2);
  delay(10);
}

// This function maintains a connection through serial with the Python data collection tool
void readSerial() {
  
  // Continuously try to read 6 bytes
  if (Serial.available() >= BUFFER_SIZE) {
    Serial.readBytes(buffer, BUFFER_SIZE);
    
    // Compare the first 2 bytes in the buffer to 0xAB (the start bits) so that we initiate the measurement
    if (memcmp(&buffer, (const void*) 0xAB, 2)) {
      // Copy over the final 4 bytes in the buffer to "amount" so that we know how many measurements to perform
      uint32_t amount;
      memcpy(&amount, &buffer[2], sizeof(amount));

      setLedGreen();
      // Send the regulator value once
      printRegulatorValue();
      for (uint32_t i = 0; i < amount; i++) {
        // Send the photodiode values for "amount" times
        printValues();
      }
      setLedRed();
    }
  } 
}

void setup() {
  // put your setup code here, to run once:
  regulator = new LightIntensityRegulator();

  //in-built LED
  pinMode(LED_BUILTIN, OUTPUT);
  //Red 
  pinMode(LEDR, OUTPUT);
  //Green 
  pinMode(LEDG, OUTPUT);
  //Blue
  pinMode(LEDB, OUTPUT);

  // Turining OFF the RGB LEDs
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

