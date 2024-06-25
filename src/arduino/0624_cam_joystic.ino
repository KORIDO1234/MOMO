#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;
int kpin = 5, xpin = A0, ypin = A1;
int servoPin = 10, angle = 90, height = 90;
int curr_swValue = 1, prev_swValue = 1;
bool func_change = false;

void cam_control() {
  if (Serial.available() >= 6) {
    String data = Serial.readStringUntil('\n');
    data.trim();

    if (data.length() == 6) {
      int value1 = data.substring(0, 3).toInt();
      int value2 = data.substring(3).toInt();
      if (value1 < 30) {
        value1 = 30;
      }
      if (value2 < 70) {
        value2 = 70;
      }
      else if (value2 > 130) {
        value2 = 130;
      }
      // value1과 value2 범위 제한 (0 ~ 180)
      height = constrain(value1, 0, 180);
      //value2 = constrain(value2, 0, 180);
      angle = map(value2, 50, 110, 70, 130);

      // servo1과 servo2에 각도 값 전달
      servo1.write(height);
      servo2.write(180-height);
      servo3.write(200-angle);

      Serial.print("Servo1: ");
      Serial.print(height);
      Serial.print(", Servo2: ");
      Serial.println(angle);
    }
  }
}

void joystic() {
    // 스위치 및 X, Y 축 값 읽어오기
  int xValue = analogRead(xpin);
  int yValue = analogRead(ypin);

  // X축 값 map() 함수로 0~180도로 변환하기
  //angle = map(xValue, 0, 1023, 70, 130);
  if (xValue > 768) {
    angle = angle + 5;
  }
  else if (xValue < 256) {
    angle = angle - 5;
  }
  
  if (angle < 70) {
    angle = 70;
  }
  else if (angle > 130) {
    angle = 130;
  }
  // y축값, 모니터 높이 제어
  if (yValue > 768) {
    height = height + 5;
  }
  else if (yValue < 256) {
    height = height - 5;
  }
  if (height < 30) {
    height = 30;
  }

  // 변환된 각도 값 시리얼 모니터에 출력
  Serial.print("Angle: ");
  Serial.println(angle);
  servo1.write(height);
  servo2.write(180- height);
  servo3.write(angle);
  delay(100);
}

void setup() {
  servo1.attach(7);  // servo1을 9번 핀에 연결
  servo3.write(height); // 서보모터 각도 초기화
  servo2.attach(8);  // servo2를 10번 핀에 연결
  servo3.write(180-height); // 서보모터 각도 초기화
  servo3.attach(10);  // servo2를 10번 핀에 연결
  servo3.write(angle); // 서보모터 각도 초기화
  pinMode(kpin, INPUT);
  digitalWrite(kpin, HIGH);

  Serial.begin(9600); // 시리얼 통신 시작
}

void loop() {
  int curr_swValue = digitalRead(kpin);
  if (curr_swValue == 0 && curr_swValue != prev_swValue){
    func_change = func_change ^ true;
    prev_swValue = curr_swValue;
  }
  else if (curr_swValue == 1 && curr_swValue != prev_swValue){
    prev_swValue = curr_swValue;
  }
  if (func_change == false) {
    cam_control();
  }
  else {
    joystic();
  }

  if (doubleclick == true) {
    // 미구현
    // int value = height*1000+angle 
    // char buffer[8]={0,};
    // itoa(value, buffer, 10);
    // strcat(buffer, "\n");
    // Serial.print(buffer);
    String data = String(height) + " " + String(angle) + "\n";
    Serial.write(data.c_str());
    delay(1000);
    //종료
  }
}