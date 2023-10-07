"""Test BLE Sensors"""
# pylint: disable=line-too-long
import logging
from unittest.mock import patch
import pytest

from homeassistant.const import PERCENTAGE
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from lennoxs30api.s30api_async import lennox_system, LENNOX_PRODUCT_TYPE_S40
from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.sensor import WTEnvSensor, lennox_wt_env_sensors
from tests.conftest import conftest_base_entity_availability, loadfile


@pytest.mark.asyncio
async def test_wt_env_sensor_text(hass, manager_system_04_furn_ac_zoning_ble: Manager):
    """Test the alert sensor"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    system.productType = LENNOX_PRODUCT_TYPE_S40

    sensor_dict = lennox_wt_env_sensors[0]
    sensor = WTEnvSensor(hass, manager, system, sensor_dict)
    assert sensor.available is False
    assert sensor.native_value is None

    data = loadfile("weather.json", system.sysId)
    manager.api.processMessage(data)

    sensor = WTEnvSensor(hass, manager, system, sensor_dict)

    assert sensor.unique_id == (system.unique_id + "wt_env_airQuality").replace("-", "")
    assert sensor.name == system.name + " " + sensor_dict["name"]
    assert sensor.available is True
    assert sensor.should_poll is False
    assert sensor.update() is True
    assert sensor.state_class is None
    assert sensor.device_class is None
    assert sensor.extra_state_attributes is None
    assert sensor.native_value == "good"
    assert sensor.entity_category is None
    assert sensor.native_unit_of_measurement is None

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id

    system.wt_env_airQuality = "error"
    assert sensor.available is False

    system.wt_env_airQuality = "moderate"
    assert sensor.available is True
    assert sensor.native_value == "moderate"

    system.wt_is_valid = False
    assert sensor.available is False


@pytest.mark.asyncio
async def test_wt_env_sensor_humidity(hass, manager_system_04_furn_ac_zoning_ble: Manager):
    """Test the wt_env sensosr"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    system.productType = LENNOX_PRODUCT_TYPE_S40

    sensor_dict = lennox_wt_env_sensors[6]
    sensor = WTEnvSensor(hass, manager, system, sensor_dict)
    assert sensor.available is False
    assert sensor.native_value is None

    data = loadfile("weather.json", system.sysId)
    manager.api.processMessage(data)

    sensor_dict = lennox_wt_env_sensors[6]
    sensor = WTEnvSensor(hass, manager, system, sensor_dict)

    assert sensor.unique_id == (system.unique_id + "wt_env_humidity").replace("-", "")
    assert sensor.name == system.name + " " + sensor_dict["name"]
    assert sensor.available is True
    assert sensor.should_poll is False
    assert sensor.update() is True
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.device_class == SensorDeviceClass.HUMIDITY
    assert sensor.extra_state_attributes is None
    assert sensor.native_value == 84
    assert sensor.native_unit_of_measurement == PERCENTAGE

    identifiers = sensor.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id

    system.wt_env_humidity = "error"
    assert sensor.native_value is None

    system.wt_env_humidity = 86
    assert sensor.native_value == 86

    system.wt_is_valid = False
    assert sensor.available is False


@pytest.mark.asyncio
async def test_wt_env_subscription(hass, manager_system_04_furn_ac_zoning_ble: Manager, caplog):
    """Test the alert sensor subscription"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    system.productType = LENNOX_PRODUCT_TYPE_S40
    data = loadfile("weather.json", system.sysId)
    manager.api.processMessage(data)

    sensor_dict = lennox_wt_env_sensors[6]
    sensor = WTEnvSensor(hass, manager, system, sensor_dict)
    await sensor.async_added_to_hass()

    with caplog.at_level(logging.DEBUG):
        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"value": "65.4"}
            system.attr_updater(update, "value", "wt_env_humidity")
            system.executeOnUpdateCallbacks()
            assert update_callback.call_count == 1
            assert sensor.native_value == 65.0
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "sensor_value_update" in caplog.messages[1]

        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            caplog.clear()
            update = {"value": False}
            system.attr_updater(update, "value", "wt_is_valid")
            system.executeOnUpdateCallbacks()
            assert update_callback.call_count == 1
            assert sensor.available is False
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "sensor_value_update" in caplog.messages[1]

    update = {"value": True}
    system.attr_updater(update, "value", "wt_is_valid")
    system.executeOnUpdateCallbacks()
    conftest_base_entity_availability(manager, system, sensor)
