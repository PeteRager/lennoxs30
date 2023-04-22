"""Test for BLE device commstatus"""
# pylint: disable=line-too-long
import logging
from unittest.mock import patch

from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY
from lennoxs30api.s30api_async import lennox_system, LENNOX_BLE_COMMSTATUS_AVAILABLE, LennoxBle
import pytest


from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)
from custom_components.lennoxs30.binary_sensor import BleCommStatusBinarySensor
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_binary_sensor_ble_commstatus(hass, manager_system_04_furn_ac_zoning_ble: Manager):
    """Test the binary sensor properties"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    ble_device: LennoxBle = system.ble_devices[513]

    sensor = BleCommStatusBinarySensor(hass, manager, system, ble_device)
    assert sensor.name == f"{system.name} {ble_device.deviceName} comm_status"
    assert sensor.unique_id == (system.unique_id + "_BLE_COMMSTATUS_513").replace("-", "")
    assert sensor.update() is True
    assert sensor.should_poll is False
    attrs = sensor.extra_state_attributes
    assert len(attrs) == 1
    assert attrs["commStatus"] == LENNOX_BLE_COMMSTATUS_AVAILABLE

    assert sensor.is_on is True
    assert sensor.available is True

    ble_device.commStatus = "BAD_STATUS"
    assert sensor.is_on is False
    assert sensor.available is True
    attrs = sensor.extra_state_attributes
    assert len(attrs) == 1
    assert attrs["commStatus"] == "BAD_STATUS"

    assert sensor.entity_category == "diagnostic"
    assert sensor.device_class == DEVICE_CLASS_CONNECTIVITY

    identifiers = sensor.device_info["identifiers"]
    for element in identifiers:
        assert element[0] == LENNOX_DOMAIN
        assert element[1] == system.unique_id + "_ble_513"


@pytest.mark.asyncio
async def test_binary_sensor_ble_commstatus_subscription(hass, manager_system_04_furn_ac_zoning_ble: Manager, caplog):
    """Tests the binary sensor subscription"""
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    ble_device: LennoxBle = system.ble_devices[513]

    sensor = BleCommStatusBinarySensor(hass, manager, system, ble_device)
    await sensor.async_added_to_hass()

    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch.object(sensor, "schedule_update_ha_state") as update_callback:
            ble_device.attr_updater({"commStatus": "offline"}, "commStatus")
            ble_device.execute_on_update_callbacks()
            assert update_callback.call_count == 1
            assert sensor.is_on is False
            assert sensor.available is True
            assert len(caplog.messages) == 2
            assert sensor.name in caplog.messages[1]
            assert "update_callback" in caplog.messages[1]

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        ble_device.attr_updater({"commStatus": LENNOX_BLE_COMMSTATUS_AVAILABLE}, "commStatus")
        ble_device.execute_on_update_callbacks()
        assert update_callback.call_count == 1
        assert sensor.is_on is True
        assert sensor.available is True

    with patch.object(sensor, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert sensor.available is False
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 2
        assert sensor.available is True

    conftest_base_entity_availability(manager, system, sensor)
