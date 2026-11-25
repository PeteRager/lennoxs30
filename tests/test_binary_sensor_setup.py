"""Tests binary sensor setup"""

# pylint: disable=protected-access
import logging
from collections import Counter
from unittest.mock import Mock

import pytest
from lennoxs30api.s30api_async import (
    LENNOX_OUTDOOR_UNIT_AC,
    LENNOX_OUTDOOR_UNIT_HP,
    lennox_system,
)

from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.binary_sensor import (
    S30AuxheatHighAmbientLockout,
    S30CloudConnectedStatus,
    S30ZoneAllergenDefenderActiveBinarySensor,
    S30ZoneAuxiliaryHeatBinarySensor,
    S30ZoneDefrostBinarySensor,
    S30ZoneFanRunningBinarySensor,
    S30HeatpumpLowAmbientLockout,
    S30HomeStateBinarySensor,
    S30InternetStatus,
    S30RelayServerStatus,
    async_setup_entry,
)
from custom_components.lennoxs30.binary_sensor_ble import BleBinarySensor, BleCommStatusBinarySensor
from custom_components.lennoxs30.ble_device_21p02 import lennox_21p02_binary_sensors
from custom_components.lennoxs30.ble_device_22v25 import lennox_22v25_binary_sensors
from custom_components.lennoxs30.const import MANAGER
from tests.conftest import loadfile


def assert_type_counts(sensor_list, expected_counts) -> Counter[type]:
    """Assert entity counts by type."""
    type_counts = Counter(type(entity) for entity in sensor_list)
    for entity_type, expected_count in expected_counts.items():
        assert type_counts[entity_type] == expected_count
    return type_counts


@pytest.mark.asyncio()
async def test_async_binary_sensor_setup_entry(hass, manager: Manager, caplog):
    """Test the binary sensor setup"""
    system: lennox_system = manager.api.system_list[0]
    entry = manager.config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}
    active_zones = sum(1 for zone in system.zone_list if zone.is_zone_active())

    assert system.outdoorUnitType != LENNOX_OUTDOOR_UNIT_HP
    manager.api.isLANConnection = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert_type_counts(
        sensor_list,
        {
            S30HomeStateBinarySensor: 1,
            S30ZoneAllergenDefenderActiveBinarySensor: active_zones,
            S30ZoneFanRunningBinarySensor: active_zones,
            S30ZoneAuxiliaryHeatBinarySensor: active_zones,
            S30ZoneDefrostBinarySensor: active_zones,
            S30InternetStatus: 1,
            S30RelayServerStatus: 1,
        },
    )

    manager.api.isLANConnection = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert_type_counts(
        sensor_list,
        {
            S30HomeStateBinarySensor: 1,
            S30ZoneAllergenDefenderActiveBinarySensor: active_zones,
            S30ZoneFanRunningBinarySensor: active_zones,
            S30ZoneAuxiliaryHeatBinarySensor: active_zones,
            S30ZoneDefrostBinarySensor: active_zones,
            S30CloudConnectedStatus: 1,
        },
    )

    system.outdoorUnitType = LENNOX_OUTDOOR_UNIT_HP
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert_type_counts(
        sensor_list,
        {
            S30HomeStateBinarySensor: 1,
            S30ZoneAllergenDefenderActiveBinarySensor: active_zones,
            S30ZoneFanRunningBinarySensor: active_zones,
            S30ZoneAuxiliaryHeatBinarySensor: active_zones,
            S30ZoneDefrostBinarySensor: active_zones,
            S30CloudConnectedStatus: 1,
            S30HeatpumpLowAmbientLockout: 1,
            S30AuxheatHighAmbientLockout: 1,
        },
    )

    # BLE Sensors
    message = loadfile("system_04_furn_ac_zoning_ble.json", system.sysId)
    system.processMessage(message)
    system.outdoorUnitType = LENNOX_OUTDOOR_UNIT_AC
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    non_tstat_ble_devices = sum(1 for ble_device in system.ble_devices.values() if ble_device.deviceType != "tstat")
    baseline_counts = assert_type_counts(
        sensor_list,
        {
            S30HomeStateBinarySensor: 1,
            S30ZoneAllergenDefenderActiveBinarySensor: active_zones,
            S30ZoneFanRunningBinarySensor: active_zones,
            S30ZoneAuxiliaryHeatBinarySensor: active_zones,
            S30ZoneDefrostBinarySensor: active_zones,
            S30CloudConnectedStatus: 1,
            BleCommStatusBinarySensor: non_tstat_ble_devices,
        },
    )
    assert baseline_counts[BleBinarySensor] == sum(
        1
        for ble_device in system.ble_devices.values()
        if ble_device.deviceType != "tstat" and ble_device.controlModelNumber in {"22V25", "21P02"}
        for _ in (lennox_22v25_binary_sensors if ble_device.controlModelNumber == "22V25" else lennox_21p02_binary_sensors)
    )

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        system.ble_devices[512].inputs.pop(4057)
        system.ble_devices[513].inputs.pop(4056)
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        error_counts = Counter(type(entity) for entity in sensor_list)
        assert error_counts[BleCommStatusBinarySensor] == baseline_counts[BleCommStatusBinarySensor]
        assert error_counts[BleBinarySensor] == baseline_counts[BleBinarySensor] - 2
        assert len(caplog.records) == 2

        assert system.ble_devices[512].deviceName in caplog.messages[0]
        assert "4057" in caplog.messages[0]
        assert "status_id" in caplog.messages[0]
        assert "occupancy" in caplog.messages[0]

        assert system.ble_devices[513].deviceName in caplog.messages[1]
        assert "4056" in caplog.messages[1]
        assert "input_id" in caplog.messages[1]
        assert "occupancy" in caplog.messages[1]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        system.ble_devices[513].controlModelNumber = "SOME_NEW_DEVICE"
        system.ble_devices.pop(512)
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        unknown_model_counts = Counter(type(entity) for entity in sensor_list)
        assert unknown_model_counts[S30HomeStateBinarySensor] == 1
        assert unknown_model_counts[S30ZoneAllergenDefenderActiveBinarySensor] == active_zones
        assert unknown_model_counts[S30ZoneFanRunningBinarySensor] == active_zones
        assert unknown_model_counts[S30ZoneAuxiliaryHeatBinarySensor] == active_zones
        assert unknown_model_counts[S30ZoneDefrostBinarySensor] == active_zones
        assert unknown_model_counts[S30CloudConnectedStatus] == 1
        assert unknown_model_counts[BleCommStatusBinarySensor] == 2
        assert unknown_model_counts[BleBinarySensor] == len(lennox_21p02_binary_sensors)
        assert len(caplog.records) == 1

        assert system.ble_devices[513].deviceName in caplog.messages[0]
        assert "SOME_NEW_DEVICE" in caplog.messages[0]
