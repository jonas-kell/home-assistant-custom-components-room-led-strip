from neopixel import Neopixel
from environment import getEnvValue

# Config Parameters

numpix = int(getEnvValue("numpix"))
stripoutpinnr = int(getEnvValue("stripoutpinnr"))
ledstripmode = str(getEnvValue("ledstripmode"))


LED_STRIP = Neopixel(
    num_leds=numpix,
    state_machine=0,
    pin=stripoutpinnr,
    mode=ledstripmode,
)


def getLEDStrip():
    global LED_STRIP
    return LED_STRIP

def getMaxPixel():
    return numpix - 1