from ledstrip import getLEDStrip, getMaxPixel
from led import blink
from server import parseUrl
import json

BLINK = False  # SET TO True FOR DEBUG

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
use_key_order = []

## INIT LIGHT STRIP
LED_STRIP = getLEDStrip()
LED_MAX_PIXEL = getMaxPixel()

def callback(method, url):
    global states

    url, params = parseUrl(url)

    blink(1, BLINK)  # show that communication happened

    if method == "GET":
        if url == "/check_connect":
            return '{"status": "success"} \n'
        if url == "/query":
            try:
                use_id = str(params["id"])
            except Exception as ex:
                print(
                    f"ERROR: Parsing arguments in /init due to exception {type(ex).__name__}, {str(ex.args)}"
                )
                return '{"status": "error"}'
            
            state = get_state_and_assert_key_initialized(use_id)
            print(state)

            return f'{{"status": "success", "state": {str(state["state"]).lower()}, "brightness": {state["brightness"]}, "red": {state["red"]}, "green": {state["green"]}, "blue": {state["blue"]}}} \n'

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

            new_id = f"if{index_from}it{index_to}"

            # init new
            state = get_state_and_assert_key_initialized(new_id)
            state["index_from"] = index_from # overwrite defaults, should not change anything on loading
            state["index_to"] = index_to # overwrite defaults, should not change anything on loading

            # save to disk
            save_state()
            print(states)

            updateLEDSTRIP() # write to strip

            return f'{{"status": "success", "id": "{new_id}"}} \n'
        if url == "/on":
            try:
                use_id = str(params["id"])
                brightness = int(params["brightness"])
                red = int(params["red"])
                green = int(params["green"])
                blue = int(params["blue"])
            except Exception as ex:
                print(
                    f"ERROR: Parsing arguments in /on due to exception {type(ex).__name__}, {str(ex.args)}"
                )
                return '{"status": "error"}'

            # modify state and save
            state = get_state_and_assert_key_initialized(use_id)
            state["state"] = True
            state["brightness"] = brightness
            state["red"] = red
            state["green"] = green
            state["blue"] = blue

            move_key_to_first(use_id)
            save_state()

            updateLEDSTRIP() # write to strip

            return '{"status": "success"} \n'
        if url == "/off":
            try:
                use_id = str(params["id"])
            except Exception as ex:
                print(
                    f"ERROR: Parsing arguments in /off due to exception {type(ex).__name__}, {str(ex.args)}"
                )
                return '{"status": "error"}'
            
            # modify state and save
            state = get_state_and_assert_key_initialized(use_id)
            state["state"] = False

            move_key_to_first(use_id)
            save_state()

            updateLEDSTRIP() # write to strip

            return '{"status": "success"} \n'

    return '{"status": "forbidden"} \n'


def get_state_and_assert_key_initialized(get_id):
    global states

    get_id = str(get_id)

    try:
        state = states[get_id]
    except:
        print("state not present try loading from file:")
        # try to load from disk
        try:
            with open("store_state.json", "r") as f:
                data = json.load(f)
                print("Loaded Data", data)

                # load all in order not to lose any
                for key in data:
                    loaded_state = data[key]
                    print("Loaded State json from file", loaded_state)

                    states[key] = {}
                    states[key]["index_from"] = int(loaded_state["index_from"])
                    states[key]["index_to"] = int(loaded_state["index_to"])
                    states[key]["state"] = bool(loaded_state["state"])
                    states[key]["brightness"] = int(loaded_state["brightness"])
                    states[key]["red"] = int(loaded_state["red"])
                    states[key]["green"] = int(loaded_state["green"])
                    states[key]["blue"] = int(loaded_state["blue"])

                    print("State parsed from file:", states[key])

                f.close()
            
            # after all things from the files have been loaded, see if they can be loaded now 
            state = states[get_id]
            
        except Exception as ex:
            print(f"Loading exception occured {type(ex).__name__}, {str(ex.args)}") # show exception without crashing

            states[get_id] = {  # DEFAULT, should not be needed
                "index_from": 0,  # bad because not known, should be overwritten
                "index_to": 10,  # bad because not known, should be overwritten
                "state": False,
                "brightness": 0,
                "red": 0,
                "green": 0,
                "blue": 0,
            }

    return states[get_id]


def save_state():
    with open("store_state.json", "w") as f:
        json.dump(states, f)
        f.close()

def updateLEDSTRIP():
    for key in list(reversed(use_key_order)):
        state = states[key]
        print(f"Updating Strip {key}")

        if state["state"]:
            LED_STRIP.brightness(state["brightness"])
            LED_STRIP.set_pixel_line(min(LED_MAX_PIXEL, state["index_from"]), min(LED_MAX_PIXEL, state["index_to"]), (state["red"], state["green"], state["blue"])) # on
        else:
            LED_STRIP.brightness(state["brightness"])
            LED_STRIP.set_pixel_line(min(LED_MAX_PIXEL, state["index_from"]), min(LED_MAX_PIXEL, state["index_to"]), (0,0,0)) # off

        LED_STRIP.show()

def move_key_to_first(key):
    global use_key_order
    if key in use_key_order:
        use_key_order.remove(key)
    use_key_order.insert(0, key)