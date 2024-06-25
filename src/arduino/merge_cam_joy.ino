#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;
int kpin = 5, xpin = A0, ypin = A1, button = 3;
int servoPin = 10, angle = 90, height = 90;
int curr_swValue = 1, prev_swValue = 1;
char func_change = 0;
int curr_button=1, prev_button=1;
int value1 = 0, value2 = 0;
int buttonState;

void control_servo() {
  servo1.write(height);
  servo2.write(180-height);
  servo3.write(200-angle);
}

void linear_control(int val_a, int val_b) {
  // value1과 value2 범위 제한 (0 ~ 180)
  height = constrain(val_a, 30, 180);
  //value2 = constrain(value2, 0, 180);
  val_b = constrain(val_b, 70, 130);
  angle = map(val_b, 70, 130, 75, 105);
  // servo1과 servo2에 각도 값 전달
  control_servo();
}

void desktop_serial(String data) {
  data.trim();

  if (data.length() == 6) {
    value1 = data.substring(0, 3).toInt();
    value2 = data.substring(3).toInt();

    linear_control(value1, value2);
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
  // y축값, 모니터 높이 제어
  if (yValue > 768) {
    height = height + 5;
  }
  else if (yValue < 256) {
    height = height - 5;
  }
  height = constrain(height, 30, 180);
  angle = constrain(angle, 80, 105);
  control_servo();
  delay(100);
}

void sw_check() {
  int curr_swValue = digitalRead(kpin);
  if (curr_swValue == 0 && curr_swValue != prev_swValue){
    if (func_change != 0){
      func_change = 0;
    }
    else {
      func_change = 1;
    }
    prev_swValue = curr_swValue;
  }
  else if (curr_swValue == 1 && curr_swValue != prev_swValue){
    prev_swValue = curr_swValue;
  }
}

void button_check() {
  curr_button = digitalRead(button);
  if (curr_button == 0 && curr_button != prev_button){
    
    if (func_change == 2){
      func_change = 3;
    }
    else {
      func_change = 2;
    }
    prev_button = curr_button;
  }
  else if (curr_button == 1 && curr_button != prev_button){
    prev_button = curr_button;
  }
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
  pinMode(button,INPUT_PULLUP);

  Serial.begin(9600); // 시리얼 통신 시작
}

void loop() {
  sw_check();
  button_check();
  
  if (func_change == 0) {
    if (Serial.available() >= 6) {
      String data = Serial.readStringUntil('\n');
      desktop_serial(data);
    }
  }
  
  else if (func_change == 1){
    joystic();
  }
  else if (func_change == 2){
    String data = String(height) + " " + String(angle) + "\n";
    Serial.write(data.c_str());
    Serial.println("저장 및 유지");
    //func_change = -1;
  }
  else if (func_change == 3){
    servo1.write(180);
    servo2.write(0);
    servo3.write(110);
    Serial.println("종료");
  }
}