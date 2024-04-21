"""Test setup of select entities"""
# pylint: disable=line-too-long
# pylint: disable=protected-access

from unittest.mock import Mock
import pytest

from lennoxs30api.s30api_async import LENNOX_VENTILATION_2_SPEED_HRV, lennox_system
from custom_components.lennoxs30 import Manager

from custom_components.lennoxs30.const import MANAGER
from custom_components.lennoxs30.select import (
    DehumidificationModeSelect,
    HumidityModeSelect,
    EquipmentParameterSelect,
    VentilationModeSelect,
    ZoneModeSelect,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_select_setup_entry(hass, manager: Manager):
    """Test the select setup"""
    system: lennox_system = manager.api.system_list[0]
    entry = manager.config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    # Nothing should be created
    system.dehumidifierType = None
    for zone in system.zone_list:
        zone.dehumidificationOption = False
        zone.humidificationOption = False
    manager.create_equipment_parameters = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.call_count == 0

    # DehumidificationModeSelect should be created
    system.dehumidifierType = "Dehumidifier"
    for zone in system.zone_list:
        zone.dehumidificationOption = False
        zone.humidificationOption = False
    manager.create_equipment_parameters = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.call_count == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], DehumidificationModeSelect)

    # HumiditySelect should be created
    system.dehumidifierType = None
    for zone in system.zone_list:
        zone.dehumidificationOption = True
        zone.humidificationOption = False
    manager.create_equipment_parameters = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.call_count == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], HumidityModeSelect)
    humselect: HumidityModeSelect = sensor_list[0]
    assert humselect._zone.id == system.zone_list[0].id

    # HumiditySelect should be created
    system.dehumidifierType = None
    for zone in system.zone_list:
        zone.dehumidificationOption = False
        zone.humidificationOption = True
    manager.create_equipment_parameters = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.call_count == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], HumidityModeSelect)
    humselect: HumidityModeSelect = sensor_list[0]
    assert humselect._zone.id == system.zone_list[0].id

    # EquipmentParameterSelect(s) should be created
    system.dehumidifierType = None
    for zone in system.zone_list:
        zone.dehumidificationOption = False
        zone.humidificationOption = False
    manager.create_equipment_parameters = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.call_count == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 15
    for i in range(0, 15):
        assert isinstance(sensor_list[i], EquipmentParameterSelect)

    # VenitlatioNModeSelect should be created
    system.dehumidifierType = None
    for zone in system.zone_list:
        zone.dehumidificationOption = False
        zone.humidificationOption = False
    manager.create_equipment_parameters = False
    system.ventilationUnitType = LENNOX_VENTILATION_2_SPEED_HRV
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.call_count == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], VentilationModeSelect)

    # ZoneModeSelect should be created
    system.dehumidifierType = None
    for zone in system.zone_list:
        zone.dehumidificationOption = False
        zone.humidificationOption = False
        zone.emergencyHeatingOption = True
    manager.create_equipment_parameters = False
    system.ventilationUnitType = None
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.call_count == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], ZoneModeSelect)