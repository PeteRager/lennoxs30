"""Test BLE Sensors"""
# pylint: disable=line-too-long
import logging
from unittest.mock import patch
import pytest

from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass

from lennoxs30api.s30api_async import lennox_system
from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import S40IAQSensor, lennox_iaq_sensors
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_iaq_sensor(hass, manager_system_04_furn_ac_zoning_ble: Manager, caplog):
    """Test the alert sensor"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    ble_device = system.ble_devices[576]
    sensor_dict = lennox_iaq_sensors[4]
    sensor = S40IAQSensor(hass, manager, system, ble_device, sensor_dict)

    assert sensor.unique_id == (system.unique_id + "_BLE_576_iaq_pm25_lta").replace("-", "")
    assert sensor.name == system.name + " " + ble_device.deviceName + " " + sensor_dict["name"]
    assert sensor.available is True
    assert sensor.should_poll is False
    assert sensor.available is True
    assert sensor.update() is True
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.device_class == SensorDeviceClass.PM25
    assert sensor.extra_state_attributes is None
    assert sensor.native_value == round(system.iaq_pm25_lta, sensor_dict["precision"])
    assert sensor.entity_category is None
    assert sensor.native_unit_of_measurement is None

    system.iaq_pm25_lta_valid = False
    assert sensor.available is False
    system.iaq_pm25_lta_valid = True
    assert sensor.available is True

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id + "_ble_576"

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.iaq_pm25_lta = "NOT_A_NUMBER"
        assert sensor.native_value is None
        assert len(caplog.messages) == 1
        assert sensor.name in caplog.messages[0]
        assert "NOT_A_NUMBER" in caplog.messages[0]
        assert "could not convert" in caplog.messages[0]

    sensor_dict = lennox_iaq_sensors[0]
    sensor = S40IAQSensor(hass, manager, system, ble_device, sensor_dict)
    assert sensor.native_value == system.iaq_mitigation_action


@pytest.mark.asyncio
async def test_iaq_subscription(hass, manager_system_04_furn_ac_zoning_ble: Manager, caplog):
    """Test the alert sensor subscription"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    ble_device = system.ble_devices[576]
    sensor_dict = lennox_iaq_sensors[4]
    sensor = S40IAQSensor(hass, manager, system, ble_device, sensor_dict)

    await sensor.async_added_to_hass()

    with caplog.at_level(logging.DEBUG):
        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"iaq_pm25_lta": 0.1234}
            system.attr_updater(update, "iaq_pm25_lta")
            system.executeOnUpdateCallbacks()
            assert update_callback.call_count == 1
            assert sensor.native_value == 0.1234
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "sensor_value_update" in caplog.messages[1]

        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"iaq_pm25_lta_valid": False}
            system.attr_updater(update, "iaq_pm25_lta_valid")
            system.executeOnUpdateCallbacks()
            assert update_callback.call_count == 1
            assert sensor.available is False
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "sensor_value_update" in caplog.messages[1]

        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"iaq_pm25_lta_valid": True}
            system.attr_updater(update, "iaq_pm25_lta_valid")
            system.executeOnUpdateCallbacks()
            assert update_callback.call_count == 1
            assert sensor.available is True

    conftest_base_entity_availability(manager, system, sensor)
