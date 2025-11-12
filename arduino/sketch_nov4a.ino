// Two options shown below:
// 1) Simple: change Stepper.setSpeed() to a higher RPM (easy but abrupt)
// 2) Recommended: use AccelStepper for smooth acceleration and higher effective speed

// --- Recommended: AccelStepper version ---
// Requires the AccelStepper library: Tools -> Manage Libraries -> install "AccelStepper"
#include <AccelStepper.h>

// Steps per one full revolution (for 28BYJ-48 this is commonly 2048 or 1536 depending on wiring/gearing)
const long stepsPerRevolution = 1536;

// Pin connection (IN1, IN3, IN2, IN4) - match your wiring to the ULN2003 board
// Use FULL4WIRE mode for the 4-wire stepper driver (ULN2003/28BYJ-48)
AccelStepper stepper(AccelStepper::FULL4WIRE, 8, 10, 9, 11);

// Tuning: increase max speed (steps/sec) and acceleration for faster motion.
// Be conservative and test: if the motor skips steps, reduce speed/acceleration or use a better driver.
const float DEFAULT_MAX_SPEED = 400.0;     // steps per second
const float DEFAULT_ACCELERATION = 200.0;  // steps per second^2

void setup() {
  // Start serial communication with PC for logging
  Serial.begin(9600);

  // Configure the stepper motion parameters
  stepper.setMaxSpeed(DEFAULT_MAX_SPEED);
  stepper.setAcceleration(DEFAULT_ACCELERATION);

  Serial.println("Setup complete. AccelStepper configured.");
}

void loop() {
  // Check for incoming serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'M') {
      Serial.println("M received, starting sequence...");
      moveMotorSequence();
      Serial.println("Sequence complete.");
    }
  }
}

// Full sequence: move, wait, and return to base using AccelStepper (smooth motion)
void moveMotorSequence() {
  // 1) Move forward one revolution
  Serial.println("Moving to target...");
  stepper.moveTo(stepsPerRevolution);
  while (stepper.distanceToGo() != 0) {
    stepper.run(); // non-blocking step until position reached
  }

  // 2) Wait
  Serial.println("Waiting...");
  delay(3000);

  // 3) Return
  Serial.println("Returning to base...");
  stepper.moveTo(0);
  while (stepper.distanceToGo() != 0) {
    stepper.run();
  }
}

/*
Notes / Tips:
- If you want a very quick test, increase DEFAULT_MAX_SPEED (e.g., 800) and DEFAULT_ACCELERATION.
- If the motor loses torque or skips steps, lower speed/accel or use a dedicated stepper driver with more current.
- Alternatively, the original Stepper library approach can be made slightly faster by
  increasing myStepper.setSpeed(15) to a larger value (RPM). That approach is simpler but
  does not provide acceleration control and is more likely to skip steps at high speed.
*/
