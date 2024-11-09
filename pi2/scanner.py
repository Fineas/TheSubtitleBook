import RPi.GPIO as GPIO
import time

class Servo:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 50)
        self.pwm.start(0)

    def turn_page(self, angle):
        duty = angle / 18 + 2
        GPIO.output(self.pin, True)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(1)
        GPIO.output(self.pin, False)
        self.pwm.ChangeDutyCycle(0)

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup()