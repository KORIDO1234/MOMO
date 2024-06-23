#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

void setup() {
  Serial.begin(9600);
  servo1.attach(7);  // servo1을 9번 핀에 연결
  servo2.attach(8);  // servo2를 10번 핀에 연결
  servo3.attach(10);  // servo2를 10번 핀에 연결
}

void loop() {
  if (Serial.available() >= 6) {
    String data = Serial.readStringUntil('\n');
    data.trim();

    if (data.length() == 6) {
      int value1 = data.substring(0, 3).toInt();
      int value2 = data.substring(3).toInt();

      // value1과 value2 범위 제한 (0 ~ 180)
      value1 = constrain(value1, 0, 180);
      value2 = constrain(value2, 0, 180);

      // servo1과 servo2에 각도 값 전달
      servo1.write(value1);
      servo2.write(180-value1);
      servo3.write(value2);

      Serial.print("Servo1: ");
      Serial.print(value1);
      Serial.print(", Servo2: ");
      Serial.println(value2);
    }
  }
}