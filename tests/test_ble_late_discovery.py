"""Tests BLE devices that are discovered after the platforms are setup"""

# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=line-too-long
from unittest.mock import Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.binary_sensor import async_setup_entry as binary_sensor_async_setup_entry
from custom_components.lennoxs30.binary_sensor_ble import BleBinarySensor, BleCommStatusBinarySensor
from custom_components.lennoxs30.const import MANAGER
from custom_components.lennoxs30.sensor import async_setup_entry as sensor_async_setup_entry
from custom_components.lennoxs30.sensor_ble import S40BleSensor
from custom_components.lennoxs30.sensor_iaq import S40IAQSensor
from tests.conftest import conftest_close_coroutine, loadfile

BLE_SENSOR_COUNT = 34
BLE_BINARY_SENSOR_COUNT = 12


def _ble_entities(add_entities: Mock) -> list:
    entities = []
    for call in add_entities.mock_calls:
        entities.extend(e for e in call.args[0] if isinstance(e, S40BleSensor | S40IAQSensor | BleBinarySensor | BleCommStatusBinarySensor))
    return entities


def _ble_registrations(mock_create_device: Mock, system: lennox_system) -> list[str]:
    prefix = f"{system.unique_id}_ble_"
    result = []
    for call in mock_create_device.mock_calls:
        for identifier in call.kwargs.get("identifiers", set()):
            if identifier[1].startswith(prefix):
                result.append(identifier[1])
    return result


async def _initialize(hass: HomeAssistant, manager: Manager, sensor_add: Mock, binary_sensor_add: Mock) -> None:
    entry = manager.config_entry
    hass.data["lennoxs30"] = {entry.unique_id: {MANAGER: manager}}

    async def forward_entry_setups(_entry, _platforms):
        await sensor_async_setup_entry(hass, entry, sensor_add)
        await binary_sensor_async_setup_entry(hass, entry, binary_sensor_add)

    with patch.object(manager, "connect_subscribe"):
        with patch.object(manager, "configuration_initialization"):
            with patch("asyncio.create_task", side_effect=conftest_close_coroutine):
                with patch.object(hass.config_entries, "async_forward_entry_setups", side_effect=forward_entry_setups):
                    await manager.s30_initialize()


@pytest.mark.asyncio()
async def test_ble_devices_arrive_after_setup(hass: HomeAssistant, manager_system_04_furn_ac_zoning: Manager):
    manager = manager_system_04_furn_ac_zoning
    system: lennox_system = manager.api.system_list[0]
    assert len(system.ble_devices) == 0

    sensor_add = Mock()
    binary_sensor_add = Mock()
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await _initialize(hass, manager, sensor_add, binary_sensor_add)
        assert len(_ble_entities(sensor_add)) == 0
        assert len(_ble_entities(binary_sensor_add)) == 0
        assert len(_ble_registrations(mock_create_device, system)) == 0

        # The BLE config message arrives after the platforms are setup
        sensor_add.reset_mock()
        binary_sensor_add.reset_mock()
        manager.api.processMessage(loadfile("system_04_furn_ac_zoning_ble.json", system.sysId))

        assert sorted(_ble_registrations(mock_create_device, system)) == [
            f"{system.unique_id}_ble_512",
            f"{system.unique_id}_ble_513",
            f"{system.unique_id}_ble_576",
        ]
        assert sensor_add.call_count == 1
        assert len(sensor_add.call_args[0][0]) == BLE_SENSOR_COUNT
        assert len(_ble_entities(sensor_add)) == BLE_SENSOR_COUNT
        assert binary_sensor_add.call_count == 1
        assert len(binary_sensor_add.call_args[0][0]) == BLE_BINARY_SENSOR_COUNT
        assert len(_ble_entities(binary_sensor_add)) == BLE_BINARY_SENSOR_COUNT

        # Reprocessing the message must not create duplicate devices or entities
        mock_create_device.reset_mock()
        sensor_add.reset_mock()
        binary_sensor_add.reset_mock()
        manager.api.processMessage(loadfile("system_04_furn_ac_zoning_ble.json", system.sysId))
        assert len(_ble_registrations(mock_create_device, system)) == 0
        assert sensor_add.call_count == 0
        assert binary_sensor_add.call_count == 0


@pytest.mark.asyncio()
async def test_ble_devices_present_at_setup(hass: HomeAssistant, manager_system_04_furn_ac_zoning_ble: Manager):
    manager = manager_system_04_furn_ac_zoning_ble
    system: lennox_system = manager.api.system_list[0]
    assert len(system.ble_devices) == 4

    sensor_add = Mock()
    binary_sensor_add = Mock()
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await _initialize(hass, manager, sensor_add, binary_sensor_add)
        assert sensor_add.call_count == 1
        assert binary_sensor_add.call_count == 1
        assert len(_ble_entities(sensor_add)) == BLE_SENSOR_COUNT
        assert len(_ble_entities(binary_sensor_add)) == BLE_BINARY_SENSOR_COUNT
        assert len(_ble_registrations(mock_create_device, system)) == 3

        # A later BLE message must not create duplicates
        mock_create_device.reset_mock()
        sensor_add.reset_mock()
        binary_sensor_add.reset_mock()
        manager._ble_devices_updated(system)
        manager.api.processMessage(loadfile("system_04_furn_ac_zoning_ble.json", system.sysId))
        assert len(_ble_registrations(mock_create_device, system)) == 0
        assert sensor_add.call_count == 0
        assert binary_sensor_add.call_count == 0


@pytest.mark.asyncio()
async def test_ble_status_update_before_config(hass: HomeAssistant, manager_system_04_furn_ac_zoning: Manager):
    manager = manager_system_04_furn_ac_zoning
    system: lennox_system = manager.api.system_list[0]

    sensor_add = Mock()
    binary_sensor_add = Mock()
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create") as mock_create_device:
        await _initialize(hass, manager, sensor_add, binary_sensor_add)
        sensor_add.reset_mock()
        binary_sensor_add.reset_mock()

        # A status only update creates the device in the API without its name or model
        status_update = {
            "SenderID": system.sysId,
            "Data": {
                "ble": {
                    "publisher": {"publisherName": "lcc"},
                    "devices": [
                        {
                            "id": 1,
                            "device": {
                                "wdn": 512,
                                "zId": 0,
                                "deviceType": "ras",
                                "devStatus": {
                                    "commStatus": "active",
                                    "inputsStatus": [
                                        {
                                            "id": 0,
                                            "status": {
                                                "name": "rssi",
                                                "vid": 4000,
                                                "format": "int8",
                                                "values": [{"id": 0, "value": "-47"}],
                                                "unit": "none",
                                            },
                                        }
                                    ],
                                },
                            },
                        }
                    ],
                }
            },
        }
        manager.api.processMessage(status_update)
        assert 512 in system.ble_devices
        assert system.ble_devices[512].controlModelNumber is None
        assert len(_ble_registrations(mock_create_device, system)) == 0
        assert sensor_add.call_count == 0
        assert binary_sensor_add.call_count == 0

        # The full config message then supplies the model and the entities are created
        manager.api.processMessage(loadfile("system_04_furn_ac_zoning_ble.json", system.sysId))
        assert len(_ble_registrations(mock_create_device, system)) == 3
        assert len(_ble_entities(sensor_add)) == BLE_SENSOR_COUNT
        assert len(_ble_entities(binary_sensor_add)) == BLE_BINARY_SENSOR_COUNT


@pytest.mark.asyncio()
async def test_ble_devices_callback_registered_once(hass: HomeAssistant, manager_system_04_furn_ac_zoning: Manager):
    manager = manager_system_04_furn_ac_zoning
    system: lennox_system = manager.api.system_list[0]
    sensor_add = Mock()
    binary_sensor_add = Mock()
    device_registry = dr.async_get(hass)
    with patch.object(device_registry, "async_get_or_create"):
        await _initialize(hass, manager, sensor_add, binary_sensor_add)
        callback_count = len(system._callbacks)
        # Simulate a reconnect, the callback must not be registered again
        await _initialize(hass, manager, sensor_add, binary_sensor_add)
        assert len(system._callbacks) == callback_count
