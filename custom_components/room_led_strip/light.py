"""Platform for light integration."""
from __future__ import annotations

import logging
import voluptuous as vol
from typing import Final, Any
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    PLATFORM_SCHEMA,
    LightEntity,
    ColorMode,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, CONF_DEVICES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback, PlatformNotReady
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

import requests

_LOGGER = logging.getLogger(__name__)

CONF_LIGHT_INDEX_FROM: Final = "light_index_from"
CONF_LIGHT_INDEX_TO: Final = "light_index_to"

DOMAIN: Final = "room_led_strip"

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_DEVICES, default={}): vol.Schema(
            {
                cv.string: {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_IP_ADDRESS): cv.string,
                    vol.Optional(CONF_LIGHT_INDEX_FROM, default="0"): cv.positive_int,
                    vol.Optional(
                        CONF_LIGHT_INDEX_TO, default="9999999"
                    ): cv.positive_int,
                }
            }
        ),
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    # Assign configuration variables.
    # The configuration check takes care they are present.

    devices = []
    for device_id, device_config in config[CONF_DEVICES].items():
        name = device_config[CONF_NAME]
        ip_address = device_config[CONF_IP_ADDRESS]
        light_index_from = device_config[CONF_LIGHT_INDEX_FROM]
        light_index_to = device_config[CONF_LIGHT_INDEX_TO]

        pico = RaspberryPiPico(
            device_id, name, ip_address, light_index_from, light_index_to
        )

        # Verify that passed in configuration works
        if not pico.assert_can_connect():
            raise PlatformNotReady(f"Could not connect to RaspberryPi Pico with custom firmware (ip: {ip_address})")
        if not pico.init_remote_state_track():
            _LOGGER.error(
                f"Could not create LED subsection (ip: {ip_address}, light_index_from: {light_index_from}, light_index_to: {light_index_to})"
            )
            continue

        _LOGGER.info(f"appended device")

        # append to devices array
        devices.append(pico)

    _LOGGER.info(f"#devices {len(devices)}")

    # Add devices
    add_entities(RoomLEDStrip(pico) for pico in devices)


class RaspberryPiPico:
    """Controls Connection to a RaspberriPi Pico with custom firmware"""

    def __init__(
        self, device_id, name, ip_address, light_index_from, light_index_to
    ) -> None:
        self._device_id = device_id
        self._name = name
        self._ip_address = ip_address
        self._light_index_from = light_index_from
        self._light_index_to = light_index_to

    def assert_can_connect(self) -> bool:
        ok, response = self.request("check_connect", {}, "get", False)

        if ok:
            _LOGGER.info(f"Asserted that Pico can connect")
            return True

        return False

    def init_remote_state_track(self) -> bool:
        ok, response = self.request(
            "init",
            {"lif": self._light_index_from, "lit": self._light_index_to},
            "post",
        )

        if not ok:
            _LOGGER.error(f"No remote state track could be set up")
            return False

        try:
            response_id = response["id"]
            if response_id != self.getID():
                _LOGGER.error(f"ID-Mismatch: {response_id} - {self.getID()}")
                return False
        except:
            _LOGGER.error(f"No id to be set was returned: {response}")
            return False

        _LOGGER.info(
            f"Created LED subsection on ip {self._ip_address} from index {self._light_index_from} to {self._light_index_to}. Now has id {self.getID()}"
        )
        return True

    def query_state(self) -> dict[str, Any]:
        state = False
        brightness = 0
        red = 0
        green = 0
        blue = 0

        ok, response = self.request(
            "query",
            {},
            "get",
        )

        parse_error = False
        if ok:
            try:
                state = bool(response["state"])
                brightness = int(response["brightness"])
                red = int(response["red"])
                green = int(response["green"])
                blue = int(response["blue"])
            except:
                parse_error = True
                _LOGGER.error(
                    f"Response malformatted, could not parse all required information from it: {response}"
                )

        ob = {
            "state": state,
            "brightness": brightness,
            "rgb_color": (red, green, blue),
        }

        if ok and not parse_error:
            _LOGGER.info(f"State Queried: {str(ob)}")

        return ob

    def turn_on(self, brightness: int, rgb_color: tuple[int, int, int]):
        ok, response = self.request(
            "on",
            {
                "brightness": brightness,
                "red": rgb_color[0],
                "green": rgb_color[1],
                "blue": rgb_color[2],
            },
            "post",
        )

        if ok:
            _LOGGER.info(f"Light turned on/updated")
            return True

        return False

    def turn_off(self):
        ok, response = self.request(
            "off",
            {},
            "post",
        )

        if ok:
            _LOGGER.info(f"Light turned on/updated")
            return True

        return False

    def request(self, route, params={}, method="get", log_connection_error=True):
        try:
            if method == "get":
                r = requests.get(
                    url=f"http://{self._ip_address}/{route}",
                    params=(params | {"id": self.getID()}),
                )
            elif method == "post":
                r = requests.post(
                    url=f"http://{self._ip_address}/{route}",
                    params=(params | {"id": self.getID()}),
                )
            else:
                raise ValueError
        except Exception as ex:
            if log_connection_error:
                _LOGGER.error(
                    f"Could not connect to RaspberryPi Pico with custom firmware on ip {self._ip_address} due to exception {type(ex).__name__}, {str(ex.args)}"
                )
            return False, {}

        if r.status_code != 200:
            _LOGGER.error(
                f"Could connect Pico to with custom firmware but returned status code {r.status_code}"
            )
            return False, {}

        try:
            response = r.json()
            status = response["status"]
        except:
            _LOGGER.error(
                f"Pico response no valid json or has the 'status' field not set: {r.text}"
            )
            return False, {}

        if status != "success":
            _LOGGER.error(f"Pico returned internal status: {str(response)}")
            return False, {}

        _LOGGER.info(f"Response from PI {self._ip_address}: {str(response)}")
        return True, response

    def getID(self):
        return f"if{self._light_index_from}it{self._light_index_to}"


class RoomLEDStrip(LightEntity):
    """Control Representation of a LED Strip"""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, pico: RaspberryPiPico) -> None:
        """Initialize a Lightable Pico Subsection"""
        self._pico = pico
        self._device_id = pico._device_id
        self._name = pico._name
        self._state = None
        self._brightness = None
        self._rgb_color = None

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def rgb_color(self):
        """Return the rgb_color of the light."""
        return self._rgb_color

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        self._pico.turn_on(
            kwargs.get(ATTR_BRIGHTNESS, 255),
            kwargs.get(ATTR_RGB_COLOR, [255, 255, 255]),
        )

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._pico.turn_off()

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        state = self._pico.query_state()
        self._state = state["state"]
        self._brightness = state["brightness"]
        self._rgb_color = state["rgb_color"]
