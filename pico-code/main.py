from time import sleep
from led import blink
from wlan import wlanConnect
from ledstrip import getLEDStrip
from server import startServer, parseUrl

BLINK = True  # SET TO True FOR DEBUG


def callback(method, url):
    url, params = parseUrl(url)

    blink(1, BLINK)  # show that communication happened

    if method == "GET":
        if url == "/check_connect":
            print(params)
            return '{"status": "success"} \n'

    if method == "POST":
        if url == "/placeholder":
            return '{"status": "success"} \n'

    return '{"status": "forbidden"} \n'


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
