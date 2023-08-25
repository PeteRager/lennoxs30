"""Tests the diagnostic sensors"""
# pylint: disable=line-too-long
# pylint: disable=protected-access
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name

import logging
from unittest.mock import patch

import pytest

from homeassistant.const import (
    PERCENTAGE,
    TEMP_FAHRENHEIT,
    FREQUENCY_HERTZ,
    ELECTRIC_CURRENT_AMPERE,
    VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE,
    ELECTRIC_POTENTIAL_VOLT,
    TIME_MINUTES,
    REVOLUTIONS_PER_MINUTE,
)
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory


from lennoxs30api.s30api_async import lennox_system, lennox_equipment_diagnostic

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.sensor import S30DiagSensor

from tests.conftest import conftest_base_entity_availability, loadfile


@pytest.mark.asyncio
async def test_diag_sensor_state(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic: lennox_equipment_diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert system.diagLevel == 0 or system.diagLevel is None
    assert s.available is False

    system.diagLevel = 2

    assert s.available is True
    assert s.state == "No"
    assert not s.extra_state_attributes
    assert s.update() is True
    assert s.should_poll is False
    assert s.name == f"{system.name}_ou_Comp._Short_Cycle_Delay_Active".replace(" ", "_")
    assert s.state_class is None
    assert s.entity_category == EntityCategory.DIAGNOSTIC

    diagnostic.value = "waiting..."
    assert s.state is None
    assert s.available is False

    equipment = system.equipment[2]
    diagnostic: lennox_equipment_diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.name == f"{system.name}_iu_{diagnostic.name}".replace(" ", "_")
    assert s.state_class == STATE_CLASS_MEASUREMENT
    assert s.state == "0.0"
    diagnostic.value = "No"
    assert s.state is None


@pytest.mark.asyncio
async def test_diag_sensor_async_added_to_hass(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    await s.async_added_to_hass()
    assert len(system._diagcallbacks) == 1
    assert system._diagcallbacks[0]["func"] == s.update_callback  # pylint: disable=comparison-with-callable
    assert system._diagcallbacks[0]["match"] == ["1_0"]

    assert len(system._callbacks) == 2
    assert system._callbacks[0]["func"] == s.system_update_callback  # pylint: disable=comparison-with-callable
    assert system._callbacks[1]["func"] == s.cloud_status_update_callback  # pylint: disable=comparison-with-callable


@pytest.mark.asyncio
async def test_diag_sensor_update_callback(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    system.diagLevel = 2
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    await s.async_added_to_hass()
    assert s.available is True
    assert s.state == "No"

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[1]
    s1 = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    await s1.async_added_to_hass()
    assert s1.available is True
    assert s1.state == "0.0"

    api = manager.api
    data = loadfile("equipments_diag_update.json", system.sysId)

    with patch.object(s, "schedule_update_ha_state") as update_callback:
        api.processMessage(data)
        assert update_callback.call_count == 1
    assert s1.available is True
    assert s.state == "Yes"
    assert s1.state == "10.0"

    with patch.object(s, "schedule_update_ha_state") as s_update_callback:
        with patch.object(s1, "schedule_update_ha_state") as s1_update_callback:
            update_set = {"diagLevel": 0}
            system.attr_updater(update_set, "diagLevel")
            system.executeOnUpdateCallbacks()
            assert s_update_callback.call_count == 1
            assert s.available is False
            assert s1_update_callback.call_count == 1
            assert s1.available is False

    with patch.object(s, "schedule_update_ha_state") as s_update_callback:
        with patch.object(s1, "schedule_update_ha_state") as s1_update_callback:
            update_set = {"diagLevel": 2}
            system.attr_updater(update_set, "diagLevel")
            system.executeOnUpdateCallbacks()
            assert s_update_callback.call_count == 1
            assert s.available is True
            assert s1_update_callback.call_count == 1
            assert s1.available is True

    conftest_base_entity_availability(manager, system, s)


@pytest.mark.asyncio
async def test_diag_sensor_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    st = f"{system.unique_id}_DS_1_Comp. Short Cycle Delay Active".replace("-", "")
    assert s.unique_id == st


@pytest.mark.asyncio
async def test_diag_sensor_unit_of_measure_device_class(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement is None
    assert s.device_class is None

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[1]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == PERCENTAGE
    assert s.device_class is None

    equipment = system.equipment[2]
    diagnostic = equipment.diagnostics[4]
    assert diagnostic.name.endswith("RPM")
    assert diagnostic.unit.strip() == ""
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.native_unit_of_measurement == REVOLUTIONS_PER_MINUTE
    assert s.device_class is None

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[9]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.native_unit_of_measurement == TEMP_FAHRENHEIT
    assert s.device_class == SensorDeviceClass.TEMPERATURE

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[12]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == TIME_MINUTES
    assert s.device_class is None

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[16]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == FREQUENCY_HERTZ
    assert s.device_class == SensorDeviceClass.FREQUENCY

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[20]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == ELECTRIC_CURRENT_AMPERE
    assert s.device_class == SensorDeviceClass.CURRENT

    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[21]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == ELECTRIC_POTENTIAL_VOLT
    assert s.device_class == SensorDeviceClass.VOLTAGE

    equipment = system.equipment[2]
    diagnostic: lennox_equipment_diagnostic = equipment.diagnostics[1]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE
    assert s.device_class is None

    diagnostic.unit = "my_custom_unit"
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == "my_custom_unit"
    assert s.device_class is None


@pytest.mark.asyncio
async def test_diag_sensor_device_info(hass, manager_system_04_furn_ac_zoning: Manager):
    manager = manager_system_04_furn_ac_zoning
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_ou"

    equipment = system.equipment[2]
    diagnostic = equipment.diagnostics[1]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    assert s.unit_of_measurement == VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE
    assert s.device_class is None

    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_iu"

    equipment = system.equipment[3]
    diagnostic = equipment.diagnostics[1]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    identifiers = s.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_BT21B13000"


@pytest.mark.asyncio
async def test_diag_sensor_device_info_no_device_errors(hass, manager_system_04_furn_ac_zoning: Manager, caplog):
    manager = manager_system_04_furn_ac_zoning
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    manager.system_equip_device_map = {}

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        identifiers = s.device_info["identifiers"]
        for x in identifiers:
            assert x[0] == LENNOX_DOMAIN
            assert x[1] == system.unique_id
        assert len(caplog.records) == 1
        assert "[1]" in caplog.messages[0]
        assert "No equipment device map found" in caplog.messages[0]


@pytest.mark.asyncio
async def test_diag_sensor_device_info_no_device_errors_1(hass, manager_system_04_furn_ac_zoning: Manager, caplog):
    manager = manager_system_04_furn_ac_zoning
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[1]
    diagnostic = equipment.diagnostics[0]
    s = S30DiagSensor(hass, manager, system, equipment, diagnostic)
    manager.system_equip_device_map[system.sysId].pop(1)

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        identifiers = s.device_info["identifiers"]
        for x in identifiers:
            assert x[0] == LENNOX_DOMAIN
            assert x[1] == system.unique_id
        assert len(caplog.records) == 1
        assert "[1]" in caplog.messages[0]
        assert "Unable to find" in caplog.messages[0]
