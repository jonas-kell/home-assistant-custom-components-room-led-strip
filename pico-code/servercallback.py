from ledstrip import getLEDStrip
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

## INIT LIGHT STRIP
" //TODO"


def callback(method, url):
    global states

    url, params = parseUrl(url)

    blink(1, BLINK)  # show that communication happened

    if method == "GET":
        if url == "/check_connect":
            return '{"status": "success"} \n'
        if url == "/query":
            try:
                use_id = int(params["id"])
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

            new_id = len(states) + 1

            # init new
            states[int(new_id)] = {
                "index_from": index_from,
                "index_to": index_to,
                "state": False,
                "brightness": 0,
                "red": 0,
                "green": 0,
                "blue": 0,
            }
            # save to disk
            save_state()
            print(states)

            return f'{{"status": "success", "id": {new_id}}} \n'
        if url == "/on":
            try:
                use_id = int(params["id"])
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
            save_state()

            return '{"status": "success"} \n'
        if url == "/off":
            try:
                use_id = int(params["id"])
            except Exception as ex:
                print(
                    f"ERROR: Parsing arguments in /off due to exception {type(ex).__name__}, {str(ex.args)}"
                )
                return '{"status": "error"}'
            
            # modify state and save
            state = get_state_and_assert_key_initialized(use_id)
            state["state"] = False
            save_state()

            return '{"status": "success"} \n'

    return '{"status": "forbidden"} \n'


def get_state_and_assert_key_initialized(get_id):
    global states

    get_id = int(get_id)

    try:
        state = states[get_id]
    except:
        print("state not present try loading from file:")
        # try to load from disk
        with open("store_state.json", "r") as f:
            try:
                data = json.load(f)
                print("Loaded Data", data)

                loaded_state = data[str(get_id)] # These functions always cast KEYS to str, bit sad, but hopefully consistent
                print("Loaded State ", loaded_state)

                states[get_id] = {}
                states[get_id]["index_from"] = int(loaded_state["index_from"])
                states[get_id]["index_to"] = int(loaded_state["index_to"])
                states[get_id]["state"] = bool(loaded_state["state"])
                states[get_id]["brightness"] = int(loaded_state["brightness"])
                states[get_id]["red"] = int(loaded_state["red"])
                states[get_id]["green"] = int(loaded_state["green"])
                states[get_id]["blue"] = int(loaded_state["blue"])

                print("State parsed from file:", states[get_id])
            except Exception as ex:
                print(f"Loading exception occured {type(ex).__name__}, {str(ex.args)}") # show exception without crashing

                states[get_id] = {  # DEFAULT, should not be needed
                    "index_from": 0,  # bad because not known
                    "index_to": 10,  # bad because not known
                    "state": False,
                    "brightness": 0,
                    "red": 0,
                    "green": 0,
                    "blue": 0,
                }

            f.close()

    return states[get_id]


def save_state():
    with open("store_state.json", "w") as f:
        json.dump(states, f)
        f.close()
