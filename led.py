from machine import Pin
from time import sleep

pin = Pin("LED", Pin.OUT)


def blink():
    pin.high()
    sleep(0.1)
    pin.low()
    sleep(0.1)
