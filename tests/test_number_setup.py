from lennoxs30api.s30api_async import (
    LENNOX_VENTILATION_DAMPER,
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import MANAGER

from custom_components.lennoxs30.number import (
    DiagnosticLevelNumber,
    DehumidificationOverCooling,
    CirculateTime,
    EquipmentParameterNumber,
    TimedVentilationNumber,
    async_setup_entry,
)

from homeassistant.helpers import entity_platform

from unittest.mock import patch

from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_async_number_setup_entry(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    # Only circulate time should be created
    system.api._isLANConnection = False
    system.dehumidifierType = None
    system.enhancedDehumidificationOvercoolingF_enable = False
    manager.create_diagnostic_sensors = False
    manager.create_inverter_power = False
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
    manager.create_diagnostic_sensors = False
    manager.create_inverter_power = False
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
    manager.create_diagnostic_sensors = False
    manager.create_inverter_power = False
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
    manager.create_diagnostic_sensors = True
    manager.create_inverter_power = True
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
    manager.create_diagnostic_sensors = False
    manager.create_inverter_power = False
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
    manager.create_diagnostic_sensors = True
    manager.create_inverter_power = False
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
    manager.create_diagnostic_sensors = False
    manager.create_inverter_power = True
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
    manager.create_diagnostic_sensors = True
    manager.create_inverter_power = True
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
    manager.create_diagnostic_sensors = True
    manager.create_inverter_power = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 4
    assert isinstance(sensor_list[0], DiagnosticLevelNumber)
    assert isinstance(sensor_list[1], DehumidificationOverCooling)
    assert isinstance(sensor_list[2], CirculateTime)
    assert isinstance(sensor_list[3], TimedVentilationNumber)

    # Only circulate time and equipment parameters should be created
    system.api._isLANConnection = False
    system.dehumidifierType = "Dehumidifier"
    system.enhancedDehumidificationOvercoolingF_enable = False
    system.ventilationUnitType = None
    manager.create_diagnostic_sensors = False
    manager.create_inverter_power = False
    manager.create_equipment_parameters = True
    async_add_entities = Mock()
    mock_async_get_current_platform = Mock()

    with patch(
        "homeassistant.helpers.entity_platform.async_get_current_platform",
        mock_async_get_current_platform,
    ):
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 41
        assert isinstance(sensor_list[0], CirculateTime)
        for i in range(1, 40):
            assert isinstance(sensor_list[i], EquipmentParameterNumber)

        ep: EquipmentParameterNumber = sensor_list[1]
        assert ep.equipment.equipment_id == 0
        assert ep.parameter.pid == 72

        assert mock_async_get_current_platform.call_count == 1
        assert mock_async_get_current_platform.call_count == 1
        service = mock_async_get_current_platform.mock_calls[1]
        assert service[0] == "().async_register_entity_service"
        service_spec = service[1]
        assert service_spec[0] == "set_zonetest_parameter"
        vol = service_spec[1]
        assert service_spec[2] == "async_set_zonetest_parameter"
