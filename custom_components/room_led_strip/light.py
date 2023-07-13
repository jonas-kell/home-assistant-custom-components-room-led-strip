"""Platform for light integration."""
from __future__ import annotations

import logging
import voluptuous as vol
from typing import Final
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    PLATFORM_SCHEMA,
    LightEntity,
    COLOR_MODE_RGB,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, CONF_DEVICES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
    for device_id, config in config[CONF_DEVICES].items():
        name = config.pop(CONF_NAME)
        ip_address = config.pop(CONF_IP_ADDRESS)
        light_index_from = config.pop(CONF_LIGHT_INDEX_FROM)
        light_index_to = config.pop(CONF_LIGHT_INDEX_TO)

        pico = RaspberryPiPico(
            device_id, name, ip_address, light_index_from, light_index_to
        )

        # Verify that passed in configuration works
        if not pico.assert_can_connect():
            _LOGGER.error(
                f"Could not connect to RaspberryPi Pico with custom firmware (ip: {ip_address})"
            )
            continue
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
        r = requests.get(
            url=f"{self._ip_address}/check_connect", params={"asd": "asdasd"}
        )

        if r.status_code == 200:
            response = r.json()

            _LOGGER.info(f"Response from PI: {str(response)}")
            return True

        _LOGGER.info(
            f"Could connect to RaspberryPi Pico with custom firmware on ip {self._ip_address}"
        )
        return False

    def init_remote_state_track(self) -> bool:
        _LOGGER.info(
            f"Created LED subsection on ip {self._ip_address} from index {self._light_index_from} to {self._light_index_to}"
        )
        return True

    def query_state(self) -> dict[str, Any]:
        return {"state": False, "brightness": 0, "rgb_color": [0, 0, 0]}

    def turn_on(self, brightness, rgb_color: tuple[int, int, int]):
        pass

    def turn_off(self):
        pass


class RoomLEDStrip(LightEntity):
    """Control Representation of a LED Strip"""

    _attr_color_mode = COLOR_MODE_RGB
    _attr_supported_color_modes = {COLOR_MODE_RGB}

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
