from time import sleep
from led import blink
from wlan import wlanConnect
from server import startServer
from servercallback import callback

BLINK = True  # SET TO True FOR DEBUG

# MAIN PROGRAM

blink(1, BLINK)

ip4 = wlanConnect()
sleep(0.1)

if BLINK:
    if ip4 != "":
        blink(2, BLINK)
    else:
        blink(1, BLINK)

startServer(ip4, callback)
