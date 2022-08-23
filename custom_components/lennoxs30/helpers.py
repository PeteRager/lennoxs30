import logging
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    FREQUENCY_HERTZ,
    ELECTRIC_CURRENT_AMPERE,
    VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE,
    ELECTRIC_POTENTIAL_VOLT,
    TIME_MINUTES,
    TIME_SECONDS,
)

from lennoxs30api.lennox_equipment import (
    lennox_equipment,
)


from . import DOMAIN, Manager

from lennoxs30api import lennox_system

_LOGGER = logging.getLogger(__name__)


def lennox_uom_to_ha_uom(unit: str) -> str:
    if unit == "F":
        return TEMP_FAHRENHEIT
    if unit == "C":
        return TEMP_CELSIUS  ## Not validated - do no know if European Units report
    if unit == "CFM":
        return VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE
    if unit == "min":
        return TIME_MINUTES
    if unit == "sec":
        return TIME_SECONDS
    if unit == "%":
        return PERCENTAGE
    if unit == "Hz":
        return FREQUENCY_HERTZ
    if unit == "V":
        return ELECTRIC_POTENTIAL_VOLT
    if unit == "A":
        return ELECTRIC_CURRENT_AMPERE
    if unit == "":
        return None
    return unit


def helper_get_equipment_device_info(
    manager: Manager, system: lennox_system, equipment_id: int
) -> dict:
    equip_device_map = manager.system_equip_device_map.get(system.sysId)
    if equip_device_map != None:
        device = equip_device_map.get(equipment_id)
        if device != None:
            return {
                "identifiers": {(DOMAIN, device.unique_name)},
            }
        _LOGGER.warning(
            f"helper_get_equipment_device_info Unable to find equipment_id [{equipment_id}] in device map sysId [{system.sysId}], please raise an issue"
        )
    else:
        _LOGGER.error(
            f"helper_get_equipment_device_info No equipment device map found for sysId [{system.sysId}] equipment_id [{equipment_id}], please raise an issue"
        )
    return {
        "identifiers": {(DOMAIN, system.unique_id())},
    }


def helper_create_equipment_entity_name(
    system: lennox_system, equipment: lennox_equipment, name: str
) -> str:
    suffix = str(equipment.equipment_name)
    if equipment.equipment_id == 1:
        suffix = "ou"
    elif equipment.equipment_id == 2:
        suffix = "iu"

    return (
        f"{system.name}_{suffix}_{name}".replace(" ", "_")
        .replace("-", "")
        .replace(".", "")
        .replace("__", "_")
    )
