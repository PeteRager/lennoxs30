"""Tests the setup of sensors"""
# pylint: disable=consider-using-enumerate
import logging
from unittest.mock import Mock
import pytest

from homeassistant.const import UnitOfTemperature

from lennoxs30api.s30api_async import (
    LENNOX_STATUS_NOT_EXIST,
    LENNOX_STATUS_GOOD,
    lennox_system,
    LENNOX_PRODUCT_TYPE_S40,
)

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import MANAGER
from custom_components.lennoxs30.sensor import (
    S30ActiveAlertsList,
    S30AlertSensor,
    S30DiagSensor,
    S30HumiditySensor,
    S30InverterPowerSensor,
    S30TempSensor,
    async_setup_entry,
    S30OutdoorTempSensor,
)
from custom_components.lennoxs30.sensor_ble import S40BleSensor
from custom_components.lennoxs30.sensor_iaq import S40IAQSensor
from custom_components.lennoxs30.sensor_wt_env import WTEnvSensor

from tests.conftest import loadfile


@pytest.mark.asyncio
async def test_async_setup_entry(hass, manager: Manager, caplog):
    """Tests the sensor setup"""
    system: lennox_system = manager.api.system_list[0]
    entry = manager.config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    # No sensors should be created
    system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
    manager.create_inverter_power = False
    manager.create_sensors = False
    manager.create_diagnostic_sensors = False
    manager.create_alert_sensors = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 0

    # Outdoor Temperature Sensor
    system.outdoorTemperatureStatus = LENNOX_STATUS_GOOD
    manager.create_inverter_power = False
    manager.create_sensors = False
    manager.create_diagnostic_sensors = False
    manager.create_alert_sensors = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], S30OutdoorTempSensor)

    # Inverter Power Sensor
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = True
        manager.create_sensors = False
        manager.create_diagnostic_sensors = False
        async_add_entities = Mock()

        system.relayServerConnected = False
        system.internetStatus = False
        system.diagLevel = 0

        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 1
        assert isinstance(sensor_list[0], S30InverterPowerSensor)
        assert len(caplog.records) == 1
        assert "diagLevel" in caplog.messages[0]
        assert "2" in caplog.messages[0]

    # Inverter Power Sensor
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = True
        manager.create_sensors = False
        manager.create_diagnostic_sensors = False
        async_add_entities = Mock()

        system.relayServerConnected = True
        system.internetStatus = False
        system.diagLevel = 2

        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 1
        assert isinstance(sensor_list[0], S30InverterPowerSensor)
        assert len(caplog.records) == 1
        assert "relayServerConnected" in caplog.messages[0]

    # Inverter Power Sensor
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = True
        manager.create_sensors = False
        manager.create_diagnostic_sensors = False
        async_add_entities = Mock()

        system.relayServerConnected = False
        system.internetStatus = True
        system.diagLevel = 2

        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 1
        assert isinstance(sensor_list[0], S30InverterPowerSensor)
        assert len(caplog.records) == 1
        assert "internetStatus" in caplog.messages[0]

    # Inverter Power Sensor
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = True
        manager.create_sensors = False
        manager.create_diagnostic_sensors = False
        async_add_entities = Mock()
        system.relayServerConnected = False
        system.internetStatus = False
        system.diagLevel = 2
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 1
        assert isinstance(sensor_list[0], S30InverterPowerSensor)
        assert len(caplog.records) == 0

    # Tempereature and Humidity Sensors
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = False
        manager.create_sensors = True
        manager.create_diagnostic_sensors = False
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 2 * system.numberOfZones
        for i in range(0, system.numberOfZones):
            assert isinstance(sensor_list[i * 2], S30TempSensor)
            assert isinstance(sensor_list[(i * 2) + 1], S30HumiditySensor)
        assert len(caplog.records) == 0

    # Diagnostic Sensors
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = False
        manager.create_sensors = False
        manager.create_diagnostic_sensors = True
        system.diagLevel = 2
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 47
        for i in range(0, len(sensor_list)):
            assert isinstance(sensor_list[i], S30DiagSensor)
        assert len(caplog.records) == 0

    # Inverter Power Sensor Internet Connected
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = False
        manager.create_sensors = False
        manager.create_diagnostic_sensors = True
        async_add_entities = Mock()

        system.relayServerConnected = False
        system.internetStatus = True
        system.diagLevel = 2

        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 47
        for i in range(0, len(sensor_list)):
            assert isinstance(sensor_list[i], S30DiagSensor)
        assert len(caplog.records) == 1
        assert "internetStatus" in caplog.messages[0]

    # Inverter Power Sensor Diag Level Not 2
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
        manager.create_inverter_power = False
        manager.create_sensors = False
        manager.create_diagnostic_sensors = True
        async_add_entities = Mock()

        system.relayServerConnected = False
        system.internetStatus = False
        system.diagLevel = 0

        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 47
        for i in range(0, len(sensor_list)):
            assert isinstance(sensor_list[i], S30DiagSensor)
        assert len(caplog.records) == 1
        assert "diagLevel 2" in caplog.messages[0]

    # Alert Sensors
    system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
    manager.create_inverter_power = False
    manager.create_sensors = False
    manager.create_diagnostic_sensors = False
    manager.create_alert_sensors = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 2
    assert isinstance(sensor_list[0], S30AlertSensor)
    assert isinstance(sensor_list[1], S30ActiveAlertsList)

    # BLE Sensors
    message = loadfile("system_04_furn_ac_zoning_ble.json", system.sysId)
    system.processMessage(message)
    system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
    manager.create_inverter_power = False
    manager.create_sensors = False
    manager.create_diagnostic_sensors = False
    manager.create_alert_sensors = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 34
    for index in range(0, 34):
        assert isinstance(sensor_list[index], S40BleSensor | S40IAQSensor)

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        system.ble_devices[512].inputs.pop(4000)
        system.ble_devices[512].inputs.pop(4051)
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 1
        sensor_list = async_add_entities.call_args[0][0]
        assert len(sensor_list) == 32
        assert len(caplog.records) == 2

        assert system.ble_devices[512].deviceName in caplog.messages[0]
        assert "4000" in caplog.messages[0]
        assert "input_id" in caplog.messages[0]
        assert "rssi" in caplog.messages[0]

        assert system.ble_devices[512].deviceName in caplog.messages[1]
        assert "4051" in caplog.messages[1]
        assert "status_id" in caplog.messages[1]
        assert "temperature" in caplog.messages[1]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        system.ble_devices[513].controlModelNumber = "SOME_NEW_DEVICE"
        system.ble_devices.pop(512)
        system.ble_devices.pop(576)
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 0
        assert len(caplog.records) == 1

        assert system.ble_devices[513].deviceName in caplog.messages[0]
        assert "SOME_NEW_DEVICE" in caplog.messages[0]

    # Weather Sensors
    message = loadfile("weather.json", system.sysId)
    system.processMessage(message)
    system.outdoorTemperatureStatus = LENNOX_STATUS_NOT_EXIST
    manager.create_inverter_power = False
    manager.create_sensors = False
    manager.create_diagnostic_sensors = False
    manager.create_alert_sensors = False
    async_add_entities = Mock()

    # Weather only supported on S40
    assert not system.is_s40
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 0

    system.productType = LENNOX_PRODUCT_TYPE_S40
    assert system.is_s40
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1

    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 10
    for index in range(0, 10):
        assert isinstance(sensor_list[index], WTEnvSensor)

    sensor: WTEnvSensor = sensor_list[9]
    assert manager.is_metric
    assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    manager.is_metric = False
    await async_setup_entry(hass, entry, async_add_entities)
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 10
    for index in range(0, 10):
        assert isinstance(sensor_list[index], WTEnvSensor)

    sensor: WTEnvSensor = sensor_list[9]
    assert sensor.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
