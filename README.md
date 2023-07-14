# HomeAssistant Custom Components Room Led Strip

Personal Room LED Strip Integration. Install it via HACS.
Used to talk to a RaspberryPi Pico running the custom micropython code also contained in this repo.
The Pico then can drive ordinary RGB Strips like ws2811.

## To use the Pico-Dev-Environment (VS-Code):

-   Install all the extensions mentioned in `.vscode/extensions.json` (VSCode should automatically prompt you to do this)
-   Run the Command `Pico-W-Go > Configure project`
-   Connect to a "Raspberry-Pi-Pico W" that has [Micropython](https://micropython.org/) firmware already flashed ([How to do this](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html#drag-and-drop-micropython)) to serial USB
-   Move the `pi_config.env.example` to `pi_config.env` and fill in the settings
-   Run the command `Pico-W-Go > Upload Project to Pico`
-   The pico should now be operational. Try disconnecting it and connect it to a power supply. The LED should flash one indicating boot and a second time indicating network status
    -   If the second flash is a singular flash, it did not manage to connect to the wifi you specified
    -   If the second flash is a double flash, it managed to connect to the wifi. Look into your Router to find out its IP-Address

## Hacs Integration

Example `configuration.yaml` entry

```
light:
    - platform: room_led_strip
      devices:
          my_room_led_strip:
              name: My Room LED Strip
              ip_address: 192.168.2.XXX
              light_index_from: 0 #optional
              light_index_to: 9999999 #optional
```

-   `name`: Name duh
-   `ip`: The IP-Address that is used to talk to the pico (get it from your router, ideally set it to be static)
-   `light_index_from`: If you want to separate one strip into multiple individual lights, choose from what index to start (inclusive). Defaults to 0.
-   `light_index_to`: If you want to separate one strip into multiple individual lights, choose at what index to end (inclusive). Defaults to 9999999, the pico software takes the maximum number of available lights aof the strip into account, but this needs to be configured in the `pi_config.env`.
