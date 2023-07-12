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
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

CONF_LIGHT_INDEX_FROM: Final = "light_index_from"
CONF_LIGHT_INDEX_TO: Final = "light_index_to"

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_LIGHT_INDEX_FROM, default="0"): cv.positive_int,
        vol.Optional(CONF_LIGHT_INDEX_TO, default="9999999"): cv.positive_int,
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
    name = config.get(CONF_NAME)
    ip_address = config.get(CONF_IP_ADDRESS)
    light_index_from = config.get(CONF_LIGHT_INDEX_FROM)
    light_index_to = config.get(CONF_LIGHT_INDEX_TO)

    pico = RaspberryPiPico(ip_address, light_index_from, light_index_to)

    # Verify that passed in configuration works
    if pico.assert_can_connect():
        _LOGGER.error("Could not connect to RaspberryPi Pico with custom firmware")
        return
    if pico.init_remote_state_track():
        _LOGGER.error("Could not create LED subsection")
        return

    # Add devices
    add_entities([RoomLEDStrip(name, pico)])


class RaspberryPiPico:
    """Controls Connection to a RaspberriPi Pico with custom firmware"""

    def __init__(self, ip_address, light_index_from, light_index_to) -> None:
        self._ip_address = ip_address
        self._light_index_from = light_index_from
        self._light_index_to = light_index_to

    def assert_can_connect(self) -> bool:
        return True

    def init_remote_state_track(self) -> bool:
        return True

    def query_state(self) -> dict[str, Any]:
        return {"state": False, "brightness": 0, "rgb_color": [0, 0, 0]}

    def turn_on(self, brightness, rgb_color: tuple[int, int, int]):
        pass

    def turn_off(self):
        pass


class RoomLEDStrip(LightEntity):
    """Control Representation of a LED Strip"""

    def __init__(self, name: str, pico: RaspberryPiPico) -> None:
        """Initialize a Light"""
        self._pico = pico
        self._name = name
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
