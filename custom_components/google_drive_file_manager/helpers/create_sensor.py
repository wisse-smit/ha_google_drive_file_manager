from __future__ import annotations

import logging
from typing import Any, List

from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)


def _create_entity_id(name: str) -> str:
    """Return a valid `sensor.<slug>` entity_id from an arbitrary name.
    
    args:
        name (str): The name of the sensor, e.g., "Camera Backups".
    Returns:
        str: A valid entity_id, e.g., "sensor.camera_backups".
    """
    return f"sensor.{slugify(name)}"


async def async_create_or_update_sensor(
    hass: HomeAssistant,
    sensor_name: str,
    state: int | str,
    attributes: dict[str, Any] | None = None
) -> None:
    """
    Create or update a sensor that stores information in the state and attributes.

    Args:
        hass (HomeAssistant): The running Home Assistant instance.
        sensor_name (str): Friendly name chosen by the user (e.g., "Camera Backups").
        Will be slugified for the entity_id.
        state (int | str): The state to set on the sensor.
        attributes (dict[str, Any] | None): Additional attributes to set on the sensor.
    """
    entity_id = _create_entity_id(sensor_name)

    # Ensure attributes is a dict
    if not attributes:
        attributes = {}

    # Add a Home Assistant friendly_name if it's missing
    if "friendly_name" not in attributes:
        attributes["friendly_name"] = sensor_name

    # Set the state and attributes of the sensor.
    hass.states.async_set(entity_id, state, attributes)
