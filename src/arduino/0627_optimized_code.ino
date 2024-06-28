#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;
const int kpin = 5, xpin = A0, ypin = A1, buttonPin = 3;
const int MIN_HEIGHT = 30;
const int MAX_HEIGHT = 180;
const int MIN_ANGLE = 75;
const int MAX_ANGLE = 110;
const int JOYSTICK_DEADZONE_LOW = 256;
const int JOYSTICK_DEADZONE_HIGH = 768;
const int SERVO_DELAY = 100;

int height = 90;
int angle = 90;
int buttonState = 0;
char funcMode = 0;
bool startSignalReceived = false;

void controlServo() {
  height = constrain(height, MIN_HEIGHT, MAX_HEIGHT);
  angle = constrain(angle, MIN_ANGLE, MAX_ANGLE);
  servo1.write(height);
  servo2.write(180 - height);
  servo3.write(200 - angle);
}

void handleSerialInput(String data) {
  const int SERIAL_DATA_LENGTH = 6;
  if (data.length() == SERIAL_DATA_LENGTH) {
    int val1 = data.substring(0, 3).toInt();
    int val2 = data.substring(3).toInt();
    height = constrain(val1, MIN_HEIGHT, MAX_HEIGHT);
    angle = constrain(val2, MIN_ANGLE, MAX_ANGLE);
  
    controlServo();
  }
}

void joystickControl() {
  int xValue = analogRead(xpin);
  int yValue = analogRead(ypin);

  if (xValue > JOYSTICK_DEADZONE_HIGH) angle += 3;
  else if (xValue < JOYSTICK_DEADZONE_LOW) angle -= 3;

  if (yValue > JOYSTICK_DEADZONE_HIGH) height += 5;
  else if (yValue < JOYSTICK_DEADZONE_LOW) height -= 5;

  controlServo();
  delay(50);
}

void checkSwitch() {
  int curr_swValue = digitalRead(kpin);
  static int prev_swValue = 1;
  if (curr_swValue != prev_swValue) {
    if (curr_swValue == LOW) {
      funcMode = (funcMode != 0) ? 0 : 1;
    }
    prev_swValue = curr_swValue;
  }
}

void checkButton() {
  int curr_button = digitalRead(buttonPin);
  static int prev_button = 1;
  if (curr_button != prev_button) {
    if (curr_button == LOW) {
      funcMode = (buttonState == 2) ? 3 : 2;
    }
    prev_button = curr_button;
  }
}

void setup() {
  servo1.attach(7);
  servo2.attach(8);
  servo3.attach(10);
  controlServo();
  
  pinMode(kpin, INPUT);
  digitalWrite(kpin, HIGH);
  pinMode(buttonPin, INPUT_PULLUP);

  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    while (Serial.available() > 0) {
      Serial.read();
    }
    if (data == "START") {
      startSignalReceived = true;
      Serial.println("START signal received");
    } else if (data == "STOP") {
      startSignalReceived = false;
      Serial.println("STOP signal received");
      funcMode = 9; // Set to no-op mode
    } else if (startSignalReceived && funcMode == 0 && data.length() >= 6) {
      handleSerialInput(data);
      Serial.println(data);
    } else if (data == "MAN"){
      funcMode = 1;
      Serial.println("MANUAL MODE");
    }
  }

  if (!startSignalReceived) {
    return; // Halt execution until START signal is received
  }

  checkSwitch();
  checkButton();

  switch (funcMode) {
    case 0:
      buttonState = funcMode;
      break;
      Serial.println("0");
    case 1:
      buttonState = funcMode;
      joystickControl();
      break;
    case 2:
      buttonState = funcMode;
      controlServo();
      Serial.println(String(height) + "," + String(angle));
      delay(500);
      funcMode = 9;
      break;
    case 3:
      buttonState = funcMode;
      servo1.write(180);
      servo2.write(0);
      servo3.write(110);
      Serial.println("종료");
      delay(500);
      funcMode = 9;
      break;
    case 9:
      // No operation
      break;
  }
}
