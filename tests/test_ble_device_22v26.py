"""Test the Lennox 22V26 BLE repeater."""

# pylint: disable=line-too-long
# pylint: disable=protected-access
import logging

import pytest
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.helpers.entity import EntityCategory
from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.binary_sensor import _create_ble_binary_sensors
from custom_components.lennoxs30.binary_sensor_ble import BleBinarySensor, BleCommStatusBinarySensor
from custom_components.lennoxs30.sensor import _create_ble_sensors
from custom_components.lennoxs30.sensor_ble import S40BleSensor
from tests.conftest import loadfile

REPEATER_WDN = 640
SYSTEM_ID = "0000000-0000-0000-0000-000000000001"


@pytest.fixture(name="repeater_manager")
def fixture_repeater_manager(manager_system_04_furn_ac_zoning: Manager) -> Manager:
    manager_system_04_furn_ac_zoning.api.processMessage(loadfile("system_04_furn_ac_zoning_ble_repeater.json", SYSTEM_ID))
    return manager_system_04_furn_ac_zoning


@pytest.mark.asyncio()
async def test_ble_22v26_sensors(hass, repeater_manager: Manager, caplog):
    manager = repeater_manager
    system: lennox_system = manager.api.system_list[0]
    ble_device = system.ble_devices[REPEATER_WDN]
    assert ble_device.controlModelNumber == "22V26"
    assert ble_device.deviceType == "repeater"

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        sensors = _create_ble_sensors(hass, manager, system, ble_device)
        assert len(caplog.records) == 0

    assert len(sensors) == 3
    assert all(isinstance(s, S40BleSensor) for s in sensors)
    by_name = {s.name.removeprefix(f"{system.name} {ble_device.deviceName} "): s for s in sensors}
    assert set(by_name) == {"rssi", "total powered time", "ble rssi"}

    for name in ("rssi", "ble rssi"):
        sensor = by_name[name]
        assert sensor.native_value == -47
        assert sensor.device_class == "signal_strength"
        assert sensor.native_unit_of_measurement == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        assert sensor.entity_category == EntityCategory.DIAGNOSTIC

    sensor = by_name["total powered time"]
    assert sensor.unique_id == (system.unique_id + f"_BLE_{REPEATER_WDN}_4003").replace("-", "")
    assert sensor.native_value == 12891840
    assert sensor.device_class == "duration"
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC

    for sensor in sensors:
        for ids in sensor.device_info["identifiers"]:
            assert ids[1] == system.unique_id + f"_ble_{REPEATER_WDN}"


@pytest.mark.asyncio()
async def test_ble_22v26_binary_sensors(hass, repeater_manager: Manager, caplog):
    manager = repeater_manager
    system: lennox_system = manager.api.system_list[0]
    ble_device = system.ble_devices[REPEATER_WDN]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        sensors = _create_ble_binary_sensors(hass, manager, system, ble_device)
        assert len(caplog.records) == 0

    assert len(sensors) == 3
    assert isinstance(sensors[0], BleCommStatusBinarySensor)
    ble_sensors = [s for s in sensors if isinstance(s, BleBinarySensor)]
    by_name = {s.name.removeprefix(f"{system.name} {ble_device.deviceName} "): s for s in ble_sensors}
    assert set(by_name) == {"alarm_status", "device_state"}
    for sensor in ble_sensors:
        assert sensor.is_on is True
        assert sensor.entity_category == EntityCategory.DIAGNOSTIC
