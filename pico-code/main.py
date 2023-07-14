from time import sleep
from led import blink
from wlan import wlanConnect
from ledstrip import getLEDStrip
from server import startServer, parseUrl

BLINK = True  # SET TO True FOR DEBUG

states = {
    # 0: {
    #     "index_from": 0,
    #     "index_to": 0,
    #     "state": False,
    #     "brightness": 0,
    #     "red": 0,
    #     "green": 0,
    #     "blue": 0,
    # }
}


def callback(method, url):
    global states

    url, params = parseUrl(url)

    blink(1, BLINK)  # show that communication happened

    if method == "GET":
        if url == "/check_connect":
            return '{"status": "success"} \n'

    if method == "POST":
        if url == "/init":
            try:
                index_from = int(params["lif"])
                index_to = int(params["lit"])
            except Exception as ex:
                print(
                    f"ERROR: Parsing arguments in /init due to exception {type(ex).__name__}, {str(ex.args)}"
                )
                return '{"status": "error"}'

            new_id = len(states) + 1

            states[new_id] = {
                "index_from": index_from,
                "index_to": index_to,
                "state": False,
                "brightness": 0,
                "red": 0,
                "green": 0,
                "blue": 0,
            }

            print(states)

            return f'{{"status": "success", "id": {new_id}}} \n'

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
