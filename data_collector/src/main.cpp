#include <Arduino.h>
#include "diode_calibration.h"

LightIntensityRegulator* regulator;

void setup() {
  // put your setup code here, to run once:
    regulator = new LightIntensityRegulator();
}

void loop() {
  // put your main code here, to run repeatedly:
  // Serial.println("Hello World!");
  Serial.print(regulator->get_resistance());
  delay(1000);
}