from time import sleep
from led import blink
from wlan import wlanConnect
from ledstrip import getLEDStrip

for i in range(1):
    blink()

ip4 = wlanConnect()

if ip4 != "":
    for i in range(2):
        blink()
else:
    for i in range(1):
        blink()

LED_STRIP = getLEDStrip()

yellow = (255, 100, 0)
orange = (255, 50, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
red = (255, 0, 0)
white = (255, 255, 255)
color0 = red

LED_STRIP.brightness(50)
LED_STRIP.fill(orange)
LED_STRIP.set_pixel_line_gradient(3, 13, green, blue)
LED_STRIP.set_pixel_line(14, 16, red)
LED_STRIP.set_pixel(20, white)

for i in range(4):
    if color0 == red:
        color0 = yellow
        color1 = red
    else:
        color0 = red
        color1 = yellow
    LED_STRIP.set_pixel(0, color0)
    LED_STRIP.set_pixel(1, color1)
    LED_STRIP.show()
    sleep(1)

for i in range(4):
    blink()
