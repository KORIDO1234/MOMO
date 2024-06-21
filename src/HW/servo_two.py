from gpiozero import Servo
from time import sleep

PWM1 = 12
PWM2 = 13
servo1 = Servo(pin=PWM1, min_pulse_width=0.6/1000, max_pulse_width=2.4/1000)
servo2 = Servo(pin=PWM2, min_pulse_width=0.6/1000, max_pulse_width=2.4/1000)


while True:
    value = float(input('setvlaue :'))
    servo1.value = value
    servo2.value = -value
    sleep(2)

