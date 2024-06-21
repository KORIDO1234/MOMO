from gpiozero import Servo
from time import sleep

myGPIO = 12

servo = Servo(pin=myGPIO, min_pulse_width=0.6/1000, max_pulse_width=2.4/1000)



while True:
    value = float(input('setvlaue :'))
    servo.value = value
    sleep(2)

