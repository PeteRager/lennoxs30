"""Test for the helper module"""
# pylint: disable=line-too-long
import logging
import pytest
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfFrequency,
    UnitOfElectricCurrent,
    UnitOfVolumeFlowRate,
    UnitOfElectricPotential,
    UnitOfTime
)
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.helpers import (
    helper_create_equipment_entity_name,
    helper_get_equipment_device_info,
    lennox_uom_to_ha_uom,
)


def test_helpers_lennox_uom_to_ha_uom():
    """Test the conversion of unit from lennox to HA"""
    assert lennox_uom_to_ha_uom("F") == UnitOfTemperature.FAHRENHEIT
    assert lennox_uom_to_ha_uom("C") == UnitOfTemperature.CELSIUS
    assert lennox_uom_to_ha_uom("CFM") == UnitOfVolumeFlowRate.CUBIC_FEET_PER_MINUTE
    assert lennox_uom_to_ha_uom("min") == UnitOfTime.MINUTES
    assert lennox_uom_to_ha_uom("sec") == UnitOfTime.SECONDS
    assert lennox_uom_to_ha_uom("%") == PERCENTAGE
    assert lennox_uom_to_ha_uom("Hz") == UnitOfFrequency.HERTZ
    assert lennox_uom_to_ha_uom("V") == UnitOfElectricPotential.VOLT
    assert lennox_uom_to_ha_uom("A") == UnitOfElectricCurrent.AMPERE
    assert lennox_uom_to_ha_uom("") is None
    assert lennox_uom_to_ha_uom("my_custom_unit") == "my_custom_unit"


@pytest.mark.asyncio
async def test_helpers_helper_get_equipment_device_info(manager: Manager):
    """Test the helper to create device info"""
    await manager.create_devices()
    system = manager.api.system_list[0]
    device_info = helper_get_equipment_device_info(manager, system, 1)

    identifiers = device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_ou"


@pytest.mark.asyncio
async def test_helpers_helper_get_equipment_device_info_no_system(manager: Manager, caplog):
    """Test the helper to create device info"""
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
    """Test the helper to create device info"""
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
async def test_helpers_create_equipment_entity_name(manager: Manager):
    """Test the helper to create device info"""
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
