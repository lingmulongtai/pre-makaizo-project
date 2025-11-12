#include <Stepper.h>

// Fallback sketch that uses the built-in Stepper library only.
// Place this file inside the `fallback` subfolder so the Arduino IDE treats it
// as a separate sketch and does not concatenate multiple .ino files together.

// Steps per one full revolution (adjust if your motor/driver differs)
const int stepsPerRevolution = 1536;

// Pin connection (IN1, IN3, IN2, IN4 order)
Stepper myStepper(stepsPerRevolution, 8, 10, 9, 11);

void setup() {
  // Start serial communication with PC
  Serial.begin(9600);

  // Increase RPM to make the motor spin faster. Test gradually.
  // The argument is in rotations per minute (RPM) for the built-in Stepper library.
  myStepper.setSpeed(15); // try 60, 90, 120 and observe. Reduce if it skips steps.

  Serial.println("Fallback Stepper sketch started. Send 'M' over serial to run sequence.");
}

void loop() {
  // Check if data has been sent from the PC
  if (Serial.available() > 0) {
    // Read one byte of incoming data
    char command = Serial.read();

    // If the data is 'M'
    if (command == 'M') {
      // Execute the full "move, wait, return" sequence
      Serial.println("M received, starting sequence..."); // Send log to PC
      moveMotorSequence();
      Serial.println("Sequence complete."); // Report completion
    }
  }
}

// The full sequence: move, wait, and return to base
void moveMotorSequence() {
  // 1. Move to the target position (Clockwise 1 revolution)
  Serial.println("Moving to target...");
  myStepper.step(stepsPerRevolution);

  // 2. Wait for a moment (e.g., 3 seconds)
  Serial.println("Waiting...");
  delay(3000); // 3000 milliseconds = 3 seconds

  // 3. Return to the base position (Counter-clockwise 1 revolution)
  Serial.println("Returning to base...");
  myStepper.step(-stepsPerRevolution);
}
