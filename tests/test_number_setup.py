import logging
from lennoxs30api.s30api_async import (
    LENNOX_STATUS_NOT_EXIST,
    LENNOX_STATUS_GOOD,
    LENNOX_VENTILATION_DAMPER,
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import CONF_CLOUD_CONNECTION, MANAGER

from custom_components.lennoxs30.number import (
    DiagnosticLevelNumber,
    DehumidificationOverCooling,
    CirculateTime,
    TimedVentilationNumber,
    async_setup_entry,
)


from unittest.mock import Mock


@pytest.mark.asyncio
async def test_async_number_setup_entry(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    # Only circulate time should be created
    system.api._isLANConnection = False
    system.dehumidifierType = None
    system.enhancedDehumidificationOvercoolingF_enable = False
    manager._create_diagnostic_sensors = False
    manager._create_inverter_power = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], CirculateTime)

    # Only circulate time should be created
    system.api._isLANConnection = False
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = False
    manager._create_diagnostic_sensors = False
    manager._create_inverter_power = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], CirculateTime)

    # Only circulate time should be created
    system.api._isLANConnection = False
    system.dehumidifierType = None
    system.enhancedDehumidificationOvercoolingF_enable = True
    manager._create_diagnostic_sensors = False
    manager._create_inverter_power = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], CirculateTime)

    # DehumidificationOverCooling and circulate time should be created
    system.api._isLANConnection = False
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = True
    manager._create_diagnostic_sensors = True
    manager._create_inverter_power = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 2
    assert isinstance(sensor_list[0], DehumidificationOverCooling)
    assert isinstance(sensor_list[1], CirculateTime)

    # DehumidificationOverCooling and circulate time should be created
    system.api._isLANConnection = False
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = True
    manager._create_diagnostic_sensors = False
    manager._create_inverter_power = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 2
    assert isinstance(sensor_list[0], DehumidificationOverCooling)
    assert isinstance(sensor_list[1], CirculateTime)

    # DiagnosticLevelNumber, DehumidificationOverCooling and circulate time should be created
    system.api._isLANConnection = True
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = True
    manager._create_diagnostic_sensors = True
    manager._create_inverter_power = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 3
    assert isinstance(sensor_list[0], DiagnosticLevelNumber)
    assert isinstance(sensor_list[1], DehumidificationOverCooling)
    assert isinstance(sensor_list[2], CirculateTime)

    # DiagnosticLevelNumber, DehumidificationOverCooling and circulate time should be created
    system.api._isLANConnection = True
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = True
    manager._create_diagnostic_sensors = False
    manager._create_inverter_power = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 3
    assert isinstance(sensor_list[0], DiagnosticLevelNumber)
    assert isinstance(sensor_list[1], DehumidificationOverCooling)
    assert isinstance(sensor_list[2], CirculateTime)

    # DiagnosticLevelNumber, DehumidificationOverCooling and circulate time should be created
    system.api._isLANConnection = True
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = True
    manager._create_diagnostic_sensors = True
    manager._create_inverter_power = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 3
    assert isinstance(sensor_list[0], DiagnosticLevelNumber)
    assert isinstance(sensor_list[1], DehumidificationOverCooling)
    assert isinstance(sensor_list[2], CirculateTime)

    # DiagnosticLevelNumber, DehumidificationOverCooling and circulate time should be created
    system.api._isLANConnection = True
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = True
    system.ventilationUnitType = LENNOX_VENTILATION_DAMPER
    manager._create_diagnostic_sensors = True
    manager._create_inverter_power = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 4
    assert isinstance(sensor_list[0], DiagnosticLevelNumber)
    assert isinstance(sensor_list[1], DehumidificationOverCooling)
    assert isinstance(sensor_list[2], CirculateTime)
    assert isinstance(sensor_list[3], TimedVentilationNumber)
