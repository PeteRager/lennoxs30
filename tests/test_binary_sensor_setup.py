"""Tests binary sensor setup"""
# pylint: disable=protected-access
import logging
from unittest.mock import Mock
import pytest

from lennoxs30api.s30api_async import (
    lennox_system,
    LENNOX_OUTDOOR_UNIT_HP,
    LENNOX_OUTDOOR_UNIT_AC,
)
from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.binary_sensor_ble import BleBinarySensor, BleCommStatusBinarySensor
from custom_components.lennoxs30.const import MANAGER

from custom_components.lennoxs30.binary_sensor import (
    S30AuxheatHighAmbientLockout,
    S30HeatpumpLowAmbientLockout,
    S30HomeStateBinarySensor,
    S30InternetStatus,
    S30RelayServerStatus,
    S30CloudConnectedStatus,
    async_setup_entry,
)
from tests.conftest import loadfile


@pytest.mark.asyncio
async def test_async_binary_sensor_setup_entry(hass, manager: Manager, caplog):
    """test the binary sensor setup"""
    system: lennox_system = manager.api.system_list[0]
    entry = manager.config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    assert system.outdoorUnitType != LENNOX_OUTDOOR_UNIT_HP
    manager.api.isLANConnection = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 3
    assert isinstance(sensor_list[0], S30HomeStateBinarySensor)
    assert isinstance(sensor_list[1], S30InternetStatus)
    assert isinstance(sensor_list[2], S30RelayServerStatus)

    manager.api.isLANConnection = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 2
    assert isinstance(sensor_list[0], S30HomeStateBinarySensor)
    assert isinstance(sensor_list[1], S30CloudConnectedStatus)

    system.outdoorUnitType = LENNOX_OUTDOOR_UNIT_HP
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 4
    assert isinstance(sensor_list[0], S30HomeStateBinarySensor)
    assert isinstance(sensor_list[1], S30CloudConnectedStatus)
    assert isinstance(sensor_list[2], S30HeatpumpLowAmbientLockout)
    assert isinstance(sensor_list[3], S30AuxheatHighAmbientLockout)

    # BLE Sensors
    message = loadfile("system_04_furn_ac_zoning_ble.json", system.sysId)
    system.processMessage(message)
    system.outdoorUnitType = LENNOX_OUTDOOR_UNIT_AC
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 14
    assert isinstance(sensor_list[0], S30HomeStateBinarySensor)
    assert isinstance(sensor_list[1], S30CloudConnectedStatus)
    assert isinstance(sensor_list[2], BleCommStatusBinarySensor)
    assert isinstance(sensor_list[3], BleBinarySensor)
    assert isinstance(sensor_list[4], BleBinarySensor)
    assert isinstance(sensor_list[5], BleBinarySensor)
    assert isinstance(sensor_list[6], BleCommStatusBinarySensor)
    assert isinstance(sensor_list[7], BleBinarySensor)
    assert isinstance(sensor_list[8], BleBinarySensor)
    assert isinstance(sensor_list[9], BleBinarySensor)
    assert isinstance(sensor_list[10], BleCommStatusBinarySensor)
    assert isinstance(sensor_list[11], BleBinarySensor)
    assert isinstance(sensor_list[12], BleBinarySensor)
    assert isinstance(sensor_list[13], BleBinarySensor)

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        system.ble_devices[512].inputs.pop(4057)
        system.ble_devices[513].inputs.pop(4056)
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 12
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
        assert len(sensor_list) == 7
        assert len(caplog.records) == 1

        assert system.ble_devices[513].deviceName in caplog.messages[0]
        assert "SOME_NEW_DEVICE" in caplog.messages[0]
