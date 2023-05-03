/*
*  File imported from https://github.com/StijnW66/CSE3000-Gesture-Recognition
*  Modified to return the total resistance configuration.
*/

#include "Arduino.h"
#include <vector>
#include <algorithm>

// Resistor struct. Pins determine which pins should be on, value represetns the resistive value that is then reached.
struct Resistor {
    std::vector<uint8_t> pins;
    float value;
};

// Resistor comparator function for sorting in decreasing order.
bool comparator(Resistor const& a, Resistor const& b) {
  return a.value > b.value;
}

// Set available resistor values.
const Resistor resistors[] = {{{D12}, 660000}, {{D11}, 330000}, {{D10}, 100000}, {{D9}, 22000}};

// Set diode to finetune
const uint8_t diode = A0;


// Parameters for diode calibration. 
const int window = 10;
const int delay_period = 10;

// Threshold values for initial configuration
const int MINIMUM_THRESHOLD = 350;
const int MAXIMUM_THRESHOLD = 750;

// Class that handles resistor configuration.
class LightIntensityRegulator {
  public:

    // Constructor with parameters for resistors (defaults to "resisistors" defined above). Number of resistors (size) is also required (default is 4).
    LightIntensityRegulator(const Resistor* resistors = resistors, int size = 4) {
      this->resistor_index = 0;

      // Create powerset and sort
      this->size = pow(2, size);
      this->powerSet = this->createPowerSet(resistors, this->size);

      std::sort(powerSet.begin(), powerSet.end(), &comparator);

      this->initialConfiguration();
    }

    // Use a resistor that is higher than the current value. Voltage output of the OPT101, and thus the received value, will go down.
    // Returns true on success, false when the active resistor was already the highest possible.
    bool resistorUp() {
      int index = this->resistor_index - 1;
      if (index < 0) {
        // Index is not possible
        return false;
      } else {
        this->resistor_index--;
        set_resistor(this->powerSet[this->resistor_index].pins);
        return true;
      }
    }

    // Use a resistor that is lower than the current value. Voltage output of the OPT101, and thus the received value, will go down.
    // Returns true on success, false when the active resistor was already the lowest possible.
    bool resistorDown() {
      int index = this->resistor_index + 1;

      if (index >= this->size) {
        // Index is not possible
        return false;

      } else {
        this->resistor_index++;
        set_resistor(this->powerSet[this->resistor_index].pins);
        return true;
      }

    }

    // Expose the current resistor index.
    int get_resistor_index() {
      return this->resistor_index;
    }

    int get_resistance() {
      return this->powerSet[this->resistor_index].value;
    }

    void reconfigure() {
      this->initialConfiguration();
    }

  private:
    int resistor_index;
    int size;
    std::vector<Resistor> powerSet;

    // Create a powerSet of all available resistors.
    std::vector<Resistor> createPowerSet(const Resistor* set, int size) {

      std::vector<Resistor> powerSet(size);

      // Fill powerset
      for(int counter = 0; counter < size; counter++) {
        std::vector<uint8_t> pin_numbers;
        std::vector<float> values;

        for(int j = 0; j < size; j++) {
          if(counter & (1<<j)) {
            values.push_back(set[j].value);
            pin_numbers.push_back(set[j].pins.at(0)); // Since these are single resistors the pin numbers are at postion 0.
          }       
        }
        powerSet[counter] = Resistor{pin_numbers, calculate_total_resistance_series(values)};
      }
      return powerSet;
    }

    // Set a list of resistors.
    void set_resistor(const std::vector<uint8_t> indices) {
      // First unset all resistors
      
      for(uint8_t i = 0; i < sizeof(resistors)/sizeof(Resistor); i++) {
        digitalWrite(resistors[i].pins.at(0), HIGH);
      }

      // Then set all resistors
      for (unsigned int j = 0; j < indices.size(); j++) {
        digitalWrite(indices.at(j), LOW);
      }
    }

    // Calculates the total resistive value of a set of resistors.
    // 1/Rtot = 1/R1 + 1/R2 ...
    float calculate_total_resistance_paralel(std::vector<float> values) {
      float sum = 0;
      for(unsigned int i = 0; i < values.size(); i++) {
        sum += 1/values.at(i);
      }
      return 1/sum;
    }

    // Adds all resistances toghether to get the resistance in series.
    float calculate_total_resistance_series(std::vector<float> values) {
      float sum = 0;
      for(unsigned int i = 0; i < values.size(); i++) {
        sum += values.at(i);
      }
      return sum;
    }

    void initialConfiguration() {
      set_resistor(powerSet[0].pins);

      // Allow the capacitor to charge up
      delay(100);

      int reading = this->get_reading();

      // Loop trough available resistors until the value drops enough
      while (reading > MAXIMUM_THRESHOLD) {
        if (!this->resistorDown()) {
          // Required resistor does not exist, set red LED
          digitalWrite(22, LOW);
          return;

        } else {
          // Get new reading
          reading = this->get_reading();
        }
      }

      // Reading is now low enough for accurate sensing.
      if (reading < MINIMUM_THRESHOLD) {
        if (!this->resistorUp()) {
          // Required resistor does not exist, set red LED
          digitalWrite(22, LOW);
          return;
        } else {
          // System maybe configured correctly, set blue LED
          digitalWrite(24, LOW);
          return;
        }
      } else {
        // System configured correctly, set green LED
        digitalWrite(23, LOW);
        return;
      }
    }

    int get_reading() {
      delay(10);

      int read_sum = 0;
      for (int i = 0; i < window; i++) {
        read_sum += analogRead(diode);
        delay(delay_period);
      }
      return read_sum / window;
    }
};