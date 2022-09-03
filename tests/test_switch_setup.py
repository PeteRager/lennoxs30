import logging
from lennoxs30api.s30api_async import (
    LENNOX_NONE_STR,
    LENNOX_VENTILATION_DAMPER,
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import MANAGER


from unittest.mock import Mock

from custom_components.lennoxs30.switch import (
    S30AllergenDefenderSwitch,
    S30ManualAwayModeSwitch,
    S30ParameterSafetySwitch,
    S30SmartAwayEnableSwitch,
    S30VentilationSwitch,
    S30ZoningSwitch,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_switch_setup_entry(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    system.ventilationUnitType = LENNOX_NONE_STR
    manager._allergenDefenderSwitch = False
    system.numberOfZones = 1

    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 2
    assert isinstance(sensor_list[0], S30ManualAwayModeSwitch)
    assert isinstance(sensor_list[1], S30SmartAwayEnableSwitch)

    async_add_entities = Mock()
    manager._create_equipment_parameters = True
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 3
    assert isinstance(sensor_list[0], S30ManualAwayModeSwitch)
    assert isinstance(sensor_list[1], S30SmartAwayEnableSwitch)
    assert isinstance(sensor_list[2], S30ParameterSafetySwitch)
    manager._create_equipment_parameters = False

    system.ventilationUnitType = LENNOX_VENTILATION_DAMPER
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 3
    assert isinstance(sensor_list[0], S30VentilationSwitch)
    assert isinstance(sensor_list[1], S30ManualAwayModeSwitch)
    assert isinstance(sensor_list[2], S30SmartAwayEnableSwitch)

    manager._allergenDefenderSwitch = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 4
    assert isinstance(sensor_list[0], S30VentilationSwitch)
    assert isinstance(sensor_list[1], S30AllergenDefenderSwitch)
    assert isinstance(sensor_list[2], S30ManualAwayModeSwitch)
    assert isinstance(sensor_list[3], S30SmartAwayEnableSwitch)

    system.numberOfZones = 2
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 5
    assert isinstance(sensor_list[0], S30VentilationSwitch)
    assert isinstance(sensor_list[1], S30AllergenDefenderSwitch)
    assert isinstance(sensor_list[2], S30ZoningSwitch)
    assert isinstance(sensor_list[3], S30ManualAwayModeSwitch)
    assert isinstance(sensor_list[4], S30SmartAwayEnableSwitch)
