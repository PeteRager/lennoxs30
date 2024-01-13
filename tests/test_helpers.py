from logging import ERROR, WARNING
import logging
import pytest
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    FREQUENCY_HERTZ,
    ELECTRIC_CURRENT_AMPERE,
    VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE,
    ELECTRIC_POTENTIAL_VOLT,
    UnitOfTime
)
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.helpers import (
    helper_create_equipment_entity_name,
    helper_get_equipment_device_info,
    lennox_uom_to_ha_uom,
)
from custom_components.lennoxs30.number import EquipmentParameterNumber


def test_helpers_lennox_uom_to_ha_uom():
    assert lennox_uom_to_ha_uom("F") == UnitOfTemperature.FAHRENHEIT
    assert lennox_uom_to_ha_uom("C") == UnitOfTemperature.CELSIUS
    assert lennox_uom_to_ha_uom("CFM") == VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE
    assert lennox_uom_to_ha_uom("min") == UnitOfTime.MINUTES
    assert lennox_uom_to_ha_uom("sec") == UnitOfTime.SECONDS
    assert lennox_uom_to_ha_uom("%") == PERCENTAGE
    assert lennox_uom_to_ha_uom("Hz") == FREQUENCY_HERTZ
    assert lennox_uom_to_ha_uom("V") == ELECTRIC_POTENTIAL_VOLT
    assert lennox_uom_to_ha_uom("A") == ELECTRIC_CURRENT_AMPERE
    assert lennox_uom_to_ha_uom("") == None
    assert lennox_uom_to_ha_uom("my_custom_unit") == "my_custom_unit"


@pytest.mark.asyncio
async def test_helpers_helper_get_equipment_device_info(manager: Manager):
    await manager.create_devices()
    system = manager.api.system_list[0]
    device_info = helper_get_equipment_device_info(manager, system, 1)

    identifiers = device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_ou"


@pytest.mark.asyncio
async def test_helpers_helper_get_equipment_device_info_no_system(manager: Manager, caplog):
    system = manager.api.system_list[0]
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        device_info = helper_get_equipment_device_info(manager, system, 1)
        identifiers = device_info["identifiers"]
        for x in identifiers:
            assert x[0] == LENNOX_DOMAIN
            assert x[1] == system.unique_id
        assert len(caplog.records) == 1
        assert system.sysId in caplog.messages[0]
        assert "1" in caplog.messages[0]
        assert "helper_get_equipment_device_info No equipment device map" in caplog.messages[0]


@pytest.mark.asyncio
async def test_helpers_helper_get_equipment_device_info_no_device(manager: Manager, caplog):
    await manager.create_devices()
    system = manager.api.system_list[0]
    manager.system_equip_device_map[system.sysId] = {}
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        device_info = helper_get_equipment_device_info(manager, system, 1)
        identifiers = device_info["identifiers"]
        for x in identifiers:
            assert x[0] == LENNOX_DOMAIN
            assert x[1] == system.unique_id
        assert len(caplog.records) == 1
        assert system.sysId in caplog.messages[0]
        assert "1" in caplog.messages[0]
        assert "helper_get_equipment_device_info Unable to find equipment_id" in caplog.messages[0]


@pytest.mark.asyncio
async def test_helpers_create_equipment_entity_name(manager: Manager, caplog):
    await manager.create_devices()
    system = manager.api.system_list[0]
    equipment = system.equipment[0]
    assert helper_create_equipment_entity_name(system, equipment, "test") == f"{system.name}_test".replace(" ", "_")

    equipment = system.equipment[1]
    assert helper_create_equipment_entity_name(system, equipment, "test") == f"{system.name}_ou_test".replace(" ", "_")
    assert helper_create_equipment_entity_name(
        system, equipment, "test", prefix="par"
    ) == f"{system.name}_par_ou_test".replace(" ", "_")

    equipment = system.equipment[2]
    assert helper_create_equipment_entity_name(system, equipment, "test") == f"{system.name}_iu_test".replace(" ", "_")

    assert helper_create_equipment_entity_name(system, equipment, "test..") == f"{system.name}_iu_test".replace(
        " ", "_"
    )

    assert helper_create_equipment_entity_name(system, equipment, "test - h") == f"{system.name}_iu_test_h".replace(
        " ", "_"
    )
