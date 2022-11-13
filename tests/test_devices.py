"""Test config flow."""

from unittest.mock import ANY, patch
from lennoxs30api.s30api_async import lennox_zone, LENNOX_NONE_STR

import pytest
import os
import json

from custom_components.lennoxs30.const import (
    LENNOX_MFG,
    VENTILATION_EQUIPMENT_ID,
)


# from tests.common import MockConfigEntry

from custom_components.lennoxs30 import (
    DOMAIN,
    Manager,
)

from homeassistant.helpers import device_registry as dr

from custom_components.lennoxs30.device import (
    S30AuxiliaryUnit,
    S30ControllerDevice,
    S30IndoorUnit,
    S30OutdoorUnit,
    S30VentilationUnit,
)


def loadfile(name) -> json:
    script_dir = os.path.dirname(__file__) + "/messages/"
    file_path = os.path.join(script_dir, name)
    with open(file_path) as f:
        data = json.load(f)
    return data


@pytest.mark.asyncio
async def test_create_devices_multiple_times(hass, manager_2_systems: Manager, caplog):
    manager = manager_2_systems
    device_registry = dr.async_get(hass)
    system = manager.api.system_list[0]
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await manager.create_devices()

        assert len(manager.system_equip_device_map[manager.api.system_list[0].sysId]) == 3
        assert len(manager.system_equip_device_map[manager.api.system_list[1].sysId]) == 4
        assert len(manager.system_equip_device_map) == 2

        await manager.create_devices()
        assert len(manager.system_equip_device_map[manager.api.system_list[0].sysId]) == 3
        assert len(manager.system_equip_device_map[manager.api.system_list[1].sysId]) == 4
        assert len(manager.system_equip_device_map) == 2


@pytest.mark.asyncio
async def test_create_devices(hass, manager_2_systems: Manager, caplog):
    manager = manager_2_systems
    device_registry = dr.async_get(hass)
    system = manager.api.system_list[0]
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await manager.create_devices()

        assert len(manager.system_equip_device_map[manager.api.system_list[0].sysId]) == 3
        assert len(manager.system_equip_device_map[manager.api.system_list[1].sysId]) == 4
        assert len(manager.system_equip_device_map) == 2

        call = mock_create_device.mock_calls[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name
        assert call.kwargs["model"] == manager.api.system_list[0].productType
        assert call.kwargs["sw_version"] == manager.api.system_list[0].softwareVersion
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id()
        device = manager.system_equip_device_map[system.sysId][0]
        assert isinstance(device, S30ControllerDevice)
        assert device.unique_name == system.unique_id()

        call = mock_create_device.mock_calls[1]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "outside"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Heat Pump"
        assert call.kwargs["model"] == "XP20-036-230B04"
        assert call.kwargs["hw_version"] == "5821D09999"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_ou"
        device = manager.system_equip_device_map[system.sysId][1]
        assert isinstance(device, S30OutdoorUnit)
        assert device.unique_name == system.unique_id() + "_ou"

        call = mock_create_device.mock_calls[2]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Air Handler"
        assert call.kwargs["model"] == "CBA38MV-036-230-02"
        assert call.kwargs["hw_version"] == "1621B25999"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_iu"
        device = manager.system_equip_device_map[system.sysId][2]
        assert isinstance(device, S30IndoorUnit)
        assert device.unique_name == system.unique_id() + "_iu"

        call = mock_create_device.mock_calls[3]
        zone: lennox_zone = manager.api.system_list[0].zone_list[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager.api.system_list[0].name + "_" + zone.name
        assert call.kwargs["model"] == "thermostat"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == zone.unique_id


@pytest.mark.asyncio
async def test_create_devices_no_outdoor(hass, manager: Manager, caplog):
    device_registry = dr.async_get(hass)
    system = manager.api.system_list[0]
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        system.outdoorUnitType = LENNOX_NONE_STR
        system.equipment.pop(1)
        await manager.create_devices()

        assert len(manager.system_equip_device_map[system.sysId]) == 2

        call = mock_create_device.mock_calls[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name
        assert call.kwargs["model"] == manager.api.system_list[0].productType
        assert call.kwargs["sw_version"] == manager.api.system_list[0].softwareVersion
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id()
        device = manager.system_equip_device_map[system.sysId][0]
        assert isinstance(device, S30ControllerDevice)
        assert device.unique_name == system.unique_id()

        call = mock_create_device.mock_calls[1]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Air Handler"
        assert call.kwargs["model"] == "CBA38MV-036-230-02"
        assert call.kwargs["hw_version"] == "1621B25999"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_iu"
        device = manager.system_equip_device_map[system.sysId][2]
        assert isinstance(device, S30IndoorUnit)
        assert device.unique_name == system.unique_id() + "_iu"

        call = mock_create_device.mock_calls[2]
        zone: lennox_zone = manager.api.system_list[0].zone_list[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager.api.system_list[0].name + "_" + zone.name
        assert call.kwargs["model"] == "thermostat"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == zone.unique_id


@pytest.mark.asyncio
async def test_create_devices_no_indoor(hass, manager: Manager, caplog):
    device_registry = dr.async_get(hass)
    system = manager.api.system_list[0]
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        manager.api.system_list[0].indoorUnitType = LENNOX_NONE_STR
        system.equipment.pop(2)

        await manager.create_devices()

        assert len(manager.system_equip_device_map[system.sysId]) == 2

        call = mock_create_device.mock_calls[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name
        assert call.kwargs["model"] == manager.api.system_list[0].productType
        assert call.kwargs["sw_version"] == manager.api.system_list[0].softwareVersion
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id()
        device = manager.system_equip_device_map[system.sysId][0]
        assert isinstance(device, S30ControllerDevice)
        assert device.unique_name == system.unique_id()

        call = mock_create_device.mock_calls[1]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "outside"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Heat Pump"
        assert call.kwargs["model"] == "XP20-036-230B04"
        assert call.kwargs["hw_version"] == "5821D09999"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_ou"
        device = manager.system_equip_device_map[system.sysId][1]
        assert isinstance(device, S30OutdoorUnit)
        assert device.unique_name == system.unique_id() + "_ou"

        call = mock_create_device.mock_calls[2]
        zone: lennox_zone = manager.api.system_list[0].zone_list[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager.api.system_list[0].name + "_" + zone.name
        assert call.kwargs["model"] == "thermostat"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == zone.unique_id


@pytest.mark.asyncio
async def test_create_devices_furn_ac_zoning(hass, manager_system_04_furn_ac_zoning: Manager, caplog):
    manager: Manager = manager_system_04_furn_ac_zoning
    device_registry = dr.async_get(hass)
    system = manager.api.system_list[0]
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await manager.create_devices()
        call = mock_create_device.mock_calls[0]

        assert len(manager.system_equip_device_map[system.sysId]) == 5

        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name
        assert call.kwargs["model"] == manager.api.system_list[0].productType
        assert call.kwargs["sw_version"] == manager.api.system_list[0].softwareVersion
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id()

        call = mock_create_device.mock_calls[1]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "outside"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Air Conditioner"
        assert call.kwargs["model"] == "EL18XCVS036-230A01"
        assert call.kwargs["hw_version"] == "5821E06000"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_ou"
        device = manager.system_equip_device_map[system.sysId][1]
        assert isinstance(device, S30OutdoorUnit)
        assert device.unique_name == system.unique_id() + "_ou"

        call = mock_create_device.mock_calls[2]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Furnace"
        assert call.kwargs["model"] == "SLP99UH110XV60C-01"
        assert call.kwargs["hw_version"] == "5920H11000"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_iu"
        device = manager.system_equip_device_map[system.sysId][2]
        assert isinstance(device, S30IndoorUnit)
        assert device.unique_name == system.unique_id() + "_iu"

        call = mock_create_device.mock_calls[3]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Zoning Controller (zone 1 to 4)"
        assert call.kwargs["model"] == "103916-03"
        assert call.kwargs["hw_version"] == "BT21B13000"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_BT21B13000"
        device = manager.system_equip_device_map[system.sysId][3]
        assert isinstance(device, S30AuxiliaryUnit)
        assert device.unique_name == system.unique_id() + "_BT21B13000"

        call = mock_create_device.mock_calls[4]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager.api.system_list[0].name + " Ventilator"
        assert call.kwargs["model"] == "2_stage_hrv"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()
        device = manager.system_equip_device_map[system.sysId][VENTILATION_EQUIPMENT_ID]
        assert isinstance(device, S30VentilationUnit)

        call = mock_create_device.mock_calls[5]
        zone: lennox_zone = manager.api.system_list[0].zone_list[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager.api.system_list[0].name + "_" + zone.name
        assert call.kwargs["model"] == "thermostat"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == zone.unique_id

        call = mock_create_device.mock_calls[6]
        zone: lennox_zone = manager.api.system_list[0].zone_list[1]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager.api.system_list[0].name + "_" + zone.name
        assert call.kwargs["model"] == "thermostat"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == zone.unique_id

        call = mock_create_device.mock_calls[7]
        zone: lennox_zone = manager.api.system_list[0].zone_list[2]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["name"] == manager.api.system_list[0].name + "_" + zone.name
        assert call.kwargs["model"] == "thermostat"
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()

        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == zone.unique_id

        assert mock_create_device.call_count == 8


@pytest.mark.asyncio
async def test_create_device_no_equipment(hass, manager_system_04_furn_ac_zoning: Manager, caplog):
    manager = manager_system_04_furn_ac_zoning
    """Test to make sure we don't crash if no equipment is received"""
    device_registry = dr.async_get(hass)
    system = manager.api.system_list[0]
    # Wipe out the equipment list.
    system.equipment = {}
    system.ventilationUnitType = None
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await manager.create_devices()

        # Ventilators gets put in this list.
        assert len(manager.system_equip_device_map[manager.api.system_list[0].sysId]) == 0
        assert len(manager.system_equip_device_map) == 1

        call = mock_create_device.mock_calls[0]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name
        assert call.kwargs["model"] == manager.api.system_list[0].productType
        assert call.kwargs["sw_version"] == manager.api.system_list[0].softwareVersion
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id()

        call = mock_create_device.mock_calls[1]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "outside"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " " + system.outdoorUnitType
        assert call.kwargs["model"] == "air conditioner"
        assert call.kwargs["hw_version"] == None
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_ou"

        call = mock_create_device.mock_calls[2]
        identifiers = call.kwargs["identifiers"]
        assert call.kwargs["manufacturer"] == LENNOX_MFG
        assert call.kwargs["suggested_area"] == "basement"
        assert call.kwargs["name"] == manager.api.system_list[0].name + " " + system.indoorUnitType
        assert call.kwargs["model"] == "furnace"
        assert call.kwargs["hw_version"] == None
        assert "sw_version" not in call.kwargs
        assert call.kwargs["via_device"][0] == DOMAIN
        assert call.kwargs["via_device"][1] == manager.api.system_list[0].unique_id()
        for elem in identifiers:
            break
        assert elem[0] == DOMAIN
        assert elem[1] == manager.api.system_list[0].unique_id() + "_iu"


@pytest.mark.asyncio
async def test_S30VentilationUnit_device_model(hass, manager_2_systems: Manager, caplog):
    manager = manager_2_systems
    system = manager.api.system_list[1]
    s30 = S30ControllerDevice(hass, manager._config_entry, system)
    system.ventilationUnitType = "ventilation"
    vent = S30VentilationUnit(hass, manager._config_entry, system, s30)
    assert vent.device_model == "Fresh Air Damper"

    system.ventilationUnitType = "1_stage_hrv"
    vent = S30VentilationUnit(hass, manager._config_entry, system, s30)
    assert vent.device_model == "1_stage_hrv"
