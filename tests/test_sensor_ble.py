"""Test BLE Sensors"""
# pylint: disable=line-too-long
import logging
from unittest.mock import patch
import pytest

from homeassistant.const import UnitOfTemperature
from lennoxs30api.s30api_async import (
    lennox_system,
    LENNOX_BLE_COMMSTATUS_AVAILABLE,
    LENNOX_BLE_STATUS_INPUT_AVAILABLE,
)
from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import S40BleSensor, lennox_22v25_sensors
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_ble_sensor(hass, manager_system_04_furn_ac_zoning_ble: Manager, caplog):
    """Test the alert sensor"""
    manager = manager_system_04_furn_ac_zoning_ble

    system: lennox_system = manager.api.system_list[0]
    ble_device = system.ble_devices[513]
    sensor_dict = lennox_22v25_sensors[3]
    input_sensor = ble_device.inputs[sensor_dict["input_id"]]
    status_sensor = ble_device.inputs[sensor_dict["status_id"]]
    sensor = S40BleSensor(hass, manager, system, ble_device, input_sensor, status_sensor, sensor_dict)

    assert sensor.unique_id == (system.unique_id + "_BLE_513_4050").replace("-", "")
    assert sensor.name == system.name + " " + ble_device.deviceName + " " + sensor_dict["name"]
    assert sensor.available is True
    assert sensor.should_poll is False
    assert sensor.available is True
    assert sensor.update() is True
    assert sensor.state_class == "measurement"
    assert sensor.device_class == "temperature"
    assert sensor.extra_state_attributes is None
    assert sensor.native_value == 66.5
    assert sensor.entity_category is None
    assert sensor.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id + "_ble_513"

    ble_device.commStatus = "unavailable"
    assert sensor.available is False
    ble_device.commStatus = LENNOX_BLE_COMMSTATUS_AVAILABLE
    assert sensor.available is True
    status_sensor.value = "1"
    assert sensor.available is False
    status_sensor.value = LENNOX_BLE_STATUS_INPUT_AVAILABLE
    assert sensor.available is True

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        input_sensor.value = "NOT_A_NUMBER"
        assert sensor.native_value is None
        assert len(caplog.messages) == 1
        assert sensor.name in caplog.messages[0]
        assert "NOT_A_NUMBER" in caplog.messages[0]
        assert "could not convert" in caplog.messages[0]


@pytest.mark.asyncio
async def test_ble_subscription(hass, manager_system_04_furn_ac_zoning_ble: Manager, caplog):
    """Test the alert sensor subscription"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    ble_device = system.ble_devices[513]
    sensor_dict = lennox_22v25_sensors[5]
    input_sensor = ble_device.inputs[sensor_dict["input_id"]]
    status_sensor = ble_device.inputs[sensor_dict["status_id"]]
    sensor = S40BleSensor(hass, manager, system, ble_device, input_sensor, status_sensor, sensor_dict)
    await sensor.async_added_to_hass()

    with caplog.at_level(logging.DEBUG):
        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"value": "65.4"}
            input_sensor.attr_updater(update, "value")
            input_sensor.execute_on_update_callbacks()
            assert update_callback.call_count == 1
            assert sensor.native_value == 65.4
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "sensor_value_update" in caplog.messages[1]

        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"value": "1"}
            status_sensor.attr_updater(update, "value")
            status_sensor.execute_on_update_callbacks()
            assert update_callback.call_count == 1
            assert sensor.available is False
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "status_value_update" in caplog.messages[1]

        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"value": LENNOX_BLE_STATUS_INPUT_AVAILABLE}
            status_sensor.attr_updater(update, "value")
            status_sensor.execute_on_update_callbacks()
            assert update_callback.call_count == 1
            assert sensor.available is True

        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"commStatus": "bad"}
            ble_device.attr_updater(update, "commStatus")
            ble_device.execute_on_update_callbacks()
            assert update_callback.call_count == 1
            assert sensor.available is False
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "commstatus_update" in caplog.messages[1]

        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"commStatus": LENNOX_BLE_COMMSTATUS_AVAILABLE}
            ble_device.attr_updater(update, "commStatus")
            ble_device.execute_on_update_callbacks()
            assert update_callback.call_count == 1
            assert sensor.available is True

    conftest_base_entity_availability(manager, system, sensor)


@pytest.mark.asyncio
async def test_ble_sensor_diag_category(hass, manager_system_04_furn_ac_zoning_ble: Manager):
    """Test the alert sensor"""
    manager = manager_system_04_furn_ac_zoning_ble

    system: lennox_system = manager.api.system_list[0]
    ble_device = system.ble_devices[513]
    sensor_dict = lennox_22v25_sensors[0]
    input_sensor = ble_device.inputs[sensor_dict["input_id"]]
    status_sensor = None
    sensor = S40BleSensor(hass, manager, system, ble_device, input_sensor, status_sensor, sensor_dict)

    assert sensor.unique_id == (system.unique_id + "_BLE_513_4000").replace("-", "")
    assert sensor.name == system.name + " " + ble_device.deviceName + " " + sensor_dict["name"]
    assert sensor.available is True
    assert sensor.should_poll is False
    assert sensor.available is True
    assert sensor.update() is True
    assert sensor.state_class == "measurement"
    assert sensor.device_class == "signal_strength"
    assert sensor.extra_state_attributes is None
    assert sensor.native_value == -66
    assert sensor.entity_category == "diagnostic"
    assert sensor.native_unit_of_measurement == "dBm"
