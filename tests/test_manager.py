"""Tests the manager class"""
# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import asyncio
import logging
import time
from unittest import mock
from unittest.mock import patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM, METRIC_SYSTEM
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, device_registry as dr

from lennoxs30api.s30api_async import (
    lennox_system,
)

from lennoxs30api.s30exception import (
    S30Exception,
    EC_LOGIN,
    EC_CONFIG_TIMEOUT,
    EC_COMMS_ERROR,
    EC_UNAUTHORIZED,
    EC_HTTP_ERR,
)


from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_CONNECTING,
    DS_DISCONNECTED,
    DS_LOGIN_FAILED,
    DS_RETRY_WAIT,
    PLATFORMS,
    RETRY_INTERVAL_SECONDS,
    Manager,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN


@pytest.mark.asyncio
async def test_manager_configuration_initialization_cloud_offline(manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.cloud_status = "offline"
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch.object(manager, "messagePump") as messagePump:
            messagePump.return_value = False
            await manager.configuration_initialization()
            assert len(caplog.records) == 1
            assert system.sysId in caplog.messages[0]
            assert "offline" in caplog.messages[0]


@pytest.mark.asyncio
async def test_manager_configuration_initialization_cloud_online(manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.cloud_status = "online"
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch.object(manager, "messagePump") as messagePump:
            messagePump.return_value = False
            await manager.configuration_initialization()
            assert len(caplog.records) == 0


@pytest.mark.asyncio
async def test_manager_configuration_initialization(manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.cloud_status = "online"
    with caplog.at_level(logging.DEBUG):
        with patch.object(manager, "messagePump") as messagePump:
            messagePump.return_value = False
            with patch.object(system, "config_complete") as config_complete:
                with patch("asyncio.sleep") as sleep:
                    config_complete.side_effect = [False, True]
                    caplog.clear()
                    await manager.configuration_initialization()
                    assert len(caplog.records) == 3
                    assert (
                        "configuration_initialization waiting for zone config to arrive host"
                        in caplog.records[0].message
                    )
                    assert manager._ip_address in caplog.records[0].message

                    assert (
                        "configuration_initialization waiting for zone config to arrive host"
                        in caplog.records[1].message
                    )
                    assert manager._ip_address in caplog.records[1].message

                    assert sleep.call_count == 1
                    assert sleep.mock_calls[0].args[0] == 1.0

                    assert "configuration_initialization host" in caplog.records[2].message
                    assert system.sysId in caplog.records[2].message

    with caplog.at_level(logging.WARNING):
        with patch.object(manager, "messagePump") as messagePump:
            messagePump.return_value = False
            with patch.object(system, "config_complete") as config_complete:
                with patch("asyncio.sleep") as sleep:
                    config_complete.return_value = False
                    caplog.clear()
                    ex: S30Exception = None
                    try:
                        await manager.configuration_initialization()
                    except S30Exception as exc:
                        ex = exc
                    assert sleep.call_count == manager._conf_init_wait_time - 1
                    assert ex is not None
                    assert ex.error_code == EC_CONFIG_TIMEOUT
                    assert "Timeout waiting for configuration data from Lennox - this sometimes happens" in ex.message


class CloudPresence:
    """Helper class for testing"""

    def __init__(self, system: lennox_system):
        self.system = system

    def toggle_cloud_status(self):
        if self.system.cloud_status == "offline":
            self.system.cloud_status = "online"
        else:
            self.system.cloud_status = "offline"


@pytest.mark.asyncio
async def test_manager_update_cloud_presence(manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.cloud_status = "online"
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.DEBUG):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            update_system_online_cloud.return_value = False
            caplog.clear()
            await manager.update_cloud_presence()
            assert len(caplog.records) == 1
            assert "update_cloud_presence sysId" in caplog.records[0].message
            assert system.sysId in caplog.records[0].message
            assert update_system_online_cloud.call_count == 1

    manager.last_cloud_presence_poll = time.time()
    with caplog.at_level(logging.DEBUG):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            update_system_online_cloud.return_value = False
            caplog.clear()
            await manager.update_cloud_presence()
            assert len(caplog.records) == 0
            assert update_system_online_cloud.call_count == 0

    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.ERROR):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                update_system_online_cloud.side_effect = S30Exception("simulated error", 100, 1)
                caplog.clear()
                await manager.update_cloud_presence()
                assert update_system_online_cloud.call_count == 1
                assert len(caplog.records) == 1
                assert "simulated error" in caplog.messages[0]
                assert "100" in caplog.messages[0]
                assert "update_cloud_presence" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]

    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.ERROR):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                update_system_online_cloud.side_effect = ValueError()
                caplog.clear()
                await manager.update_cloud_presence()
                assert update_system_online_cloud.call_count == 1
                assert len(caplog.records) == 1
                assert "unexpected exception" in caplog.messages[0]
                assert "update_cloud_presence" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]

    # Cloud status online -> offline
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.ERROR):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                caplog.clear()
                system.cloud_status = "online"
                cp = CloudPresence(system)
                update_system_online_cloud.side_effect = cp.toggle_cloud_status
                await manager.update_cloud_presence()
                assert system.cloud_status == "offline"
                assert update_system_online_cloud.call_count == 1
                assert len(caplog.records) == 1
                assert "cloud status changed to offline for sysId" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]
                assert mock_subscribe.call_count == 0

    # Cloud status offline -> online
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                caplog.clear()
                system.cloud_status = "offline"
                cp = CloudPresence(system)
                update_system_online_cloud.side_effect = cp.toggle_cloud_status
                await manager.update_cloud_presence()
                assert system.cloud_status == "online"
                assert update_system_online_cloud.call_count == 1
                assert len(caplog.records) == 1
                assert "cloud status changed to online for sysId" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]
                assert mock_subscribe.call_count == 1

    # Cloud status offline -> online, S30exception on resubscribe
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                system.cloud_status = "offline"
                cp = CloudPresence(system)
                update_system_online_cloud.side_effect = cp.toggle_cloud_status
                mock_subscribe.side_effect = S30Exception("simulated error", 10, 0)
                await manager.update_cloud_presence()
                assert system.cloud_status == "online"
                assert update_system_online_cloud.call_count == 1
                assert update_system_online_cloud.call_count == 1

                assert len(caplog.records) == 2
                assert "cloud status changed to online for sysId" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]
                assert "update_cloud_presence resubscribe error" in caplog.messages[1]
                assert system.sysId in caplog.messages[1]
                assert manager._reinitialize is True

    # Cloud status offline -> online, exception on resubscribe
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                system.cloud_status = "offline"
                cp = CloudPresence(system)
                update_system_online_cloud.side_effect = cp.toggle_cloud_status
                mock_subscribe.side_effect = ValueError()
                await manager.update_cloud_presence()
                assert system.cloud_status == "online"
                assert update_system_online_cloud.call_count == 1
                assert mock_subscribe.call_count == 1

                assert len(caplog.records) == 2
                assert "cloud status changed to online for sysId" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]
                assert "update_cloud_presence resubscribe error unexpected exception" in caplog.messages[1]
                assert system.sysId in caplog.messages[1]
                assert manager._reinitialize is True

    # No last poll, should not poll just update counter
    manager.last_cloud_presence_poll = None
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                await manager.update_cloud_presence()
                assert update_system_online_cloud.call_count == 0
                assert mock_subscribe.call_count == 0
                assert manager.last_cloud_presence_poll is not None
                assert (
                    manager.last_cloud_presence_poll < time.time()
                    and manager.last_cloud_presence_poll > time.time() - 10.0
                )
                assert len(caplog.records) == 0
                assert manager._reinitialize is False

    # No last poll, should not poll just update counter
    manager.last_cloud_presence_poll = time.time() - 610
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as update_system_online_cloud:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                await manager.update_cloud_presence()
                assert update_system_online_cloud.call_count == 1
                assert mock_subscribe.call_count == 0
                assert manager.last_cloud_presence_poll is not None
                assert (
                    manager.last_cloud_presence_poll < time.time()
                    and manager.last_cloud_presence_poll > time.time() - 10.0
                )
                assert len(caplog.records) == 0
                assert manager._reinitialize is False


@pytest.mark.asyncio
async def test_manager_metric_units(hass: HomeAssistant, manager: Manager):
    assert hass.config.units is METRIC_SYSTEM
    assert manager.is_metric is True


@pytest.mark.asyncio
async def test_manager_us_customary_units(hass: HomeAssistant, manager_us_customary_units: Manager):
    assert hass.config.units is US_CUSTOMARY_SYSTEM
    assert manager_us_customary_units.is_metric is False


@pytest.mark.asyncio
async def test_manager_s30_initialize(hass: HomeAssistant, manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    with patch.object(manager, "updateState") as update_state:
        with patch.object(manager, "connect_subscribe") as connect_subscribe:
            with patch.object(manager, "configuration_initialization") as configuration_initialization:
                with patch("asyncio.create_task") as create_task:
                    create_task.return_value = "AWAITABLE_TASK"
                    with patch.object(manager, "create_devices") as create_devices:
                        with patch.object(hass, "async_create_task") as hass_create_task:
                            await manager.s30_initialize()

                            assert update_state.call_count == 2
                            assert update_state.mock_calls[0].args[0] == DS_CONNECTING
                            assert update_state.mock_calls[1].args[0] == DS_CONNECTED

                            assert connect_subscribe.call_count == 1
                            assert len(connect_subscribe.mock_calls[0].args) == 0

                            assert configuration_initialization.call_count == 1
                            assert len(configuration_initialization.mock_calls[0].args) == 0

                            assert create_task.call_count == 1
                            assert create_task.mock_calls[0].args[0].__name__ == "messagePump_task"
                            assert manager._retrieve_task == "AWAITABLE_TASK"
                            assert create_devices.call_count == 1
                            assert len(create_devices.mock_calls[0].args) == 0

                            assert hass_create_task.call_count == len(PLATFORMS)


@pytest.mark.asyncio
async def test_manager_s30_initialize_retry_task(manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    with patch.object(manager, "updateState") as update_state:
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "s30_initialize") as _:
                await manager.initialize_retry_task()
                assert update_state.call_count == 3
                assert update_state.mock_calls[0].args[0] == DS_RETRY_WAIT
                assert update_state.mock_calls[1].args[0] == DS_CONNECTING
                assert update_state.mock_calls[2].args[0] == DS_CONNECTED

                assert sleep.call_count == 1
                assert sleep.mock_calls[0].args[0] == RETRY_INTERVAL_SECONDS

    with patch.object(manager, "updateState") as update_state:
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "s30_initialize") as s30_initialize:
                s30_initialize.side_effect = S30Exception("bad username", EC_LOGIN, 0)
                await manager.initialize_retry_task()
                assert update_state.call_count == 3

                assert update_state.mock_calls[0].args[0] == DS_RETRY_WAIT
                assert update_state.mock_calls[1].args[0] == DS_CONNECTING
                assert update_state.mock_calls[2].args[0] == DS_LOGIN_FAILED

                assert sleep.call_count == 1
                assert sleep.mock_calls[0].args[0] == RETRY_INTERVAL_SECONDS

    with patch.object(manager, "updateState") as update_state:
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "s30_initialize") as s30_initialize:
                s30_initialize.side_effect = [
                    S30Exception("configuration timeout", EC_CONFIG_TIMEOUT, 0),
                    S30Exception("network error", EC_COMMS_ERROR, 0),
                    mock.DEFAULT,
                ]
                await manager.initialize_retry_task()
                assert update_state.call_count == 7

                assert update_state.mock_calls[0].args[0] == DS_RETRY_WAIT
                assert update_state.mock_calls[1].args[0] == DS_CONNECTING

                assert update_state.mock_calls[2].args[0] == DS_RETRY_WAIT
                assert update_state.mock_calls[3].args[0] == DS_CONNECTING

                assert update_state.mock_calls[4].args[0] == DS_RETRY_WAIT
                assert update_state.mock_calls[5].args[0] == DS_CONNECTING
                assert update_state.mock_calls[6].args[0] == DS_CONNECTED

                assert sleep.call_count == 3
                assert sleep.mock_calls[0].args[0] == RETRY_INTERVAL_SECONDS
                assert sleep.mock_calls[1].args[0] == RETRY_INTERVAL_SECONDS


@pytest.mark.asyncio
async def test_manager_connect(manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    with patch.object(manager.api, "serverConnect") as server_connect:
        await manager.connect()
        assert server_connect.call_count == 1
        assert len(server_connect.mock_calls[0].args) == 0


@pytest.mark.asyncio
async def test_manager_connect_subscribe(manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    system: lennox_system = manager.api.system_list[0]
    with patch.object(manager.api, "serverConnect") as server_connect:
        with patch.object(manager.api, "subscribe") as subscribe:
            await manager.connect_subscribe()
            assert server_connect.call_count == 1
            assert len(server_connect.mock_calls[0].args) == 0

            assert subscribe.call_count == 1
            assert len(subscribe.mock_calls[0].args) == 1
            assert subscribe.mock_calls[0].args[0] == system


@pytest.mark.asyncio
async def test_manager_reinitialize_task(manager_us_customary_units: Manager, caplog):
    manager = manager_us_customary_units
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch.object(manager, "updateState") as update_state:
            with patch.object(manager, "connect_subscribe") as connect_subscribe:
                with patch.object(manager, "messagePump_task") as messagePump_task:
                    with patch("asyncio.create_task") as create_task:
                        create_task.return_value = "AWAITABLE_TASK"
                        await manager.reinitialize_task()
                        assert connect_subscribe.call_count == 1
                        assert len(connect_subscribe.mock_calls[0].args) == 0
                        assert update_state.call_count == 2
                        assert update_state.mock_calls[0].args[0] == DS_CONNECTING
                        assert update_state.mock_calls[1].args[0] == DS_CONNECTED

                        assert create_task.call_count == 1
                        assert messagePump_task.call_count == 1
                        assert manager._retrieve_task == "AWAITABLE_TASK"
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(manager, "updateState") as update_state:
            with patch.object(manager, "messagePump_task") as messagePump_task:
                with patch.object(manager, "connect_subscribe") as connect_subscribe:
                    connect_subscribe.side_effect = [S30Exception("Network Error", EC_COMMS_ERROR, 0), mock.DEFAULT]
                    with patch("asyncio.create_task") as create_task:
                        with patch("asyncio.sleep") as sleep:
                            await manager.reinitialize_task()
                            assert connect_subscribe.call_count == 2
                            assert len(connect_subscribe.mock_calls[0].args) == 0
                            assert update_state.call_count == 4
                            assert update_state.mock_calls[0].args[0] == DS_CONNECTING
                            assert update_state.mock_calls[1].args[0] == DS_RETRY_WAIT
                            assert update_state.mock_calls[2].args[0] == DS_CONNECTING
                            assert update_state.mock_calls[3].args[0] == DS_CONNECTED

                            assert sleep.call_count == 1
                            assert sleep.mock_calls[0].args[0] == RETRY_INTERVAL_SECONDS

                            assert create_task.call_count == 1
                            assert messagePump_task.call_count == 1

                            assert len(caplog.records) == 1
                            assert "reinitialize_task host" in caplog.records[0].message
                            assert manager._ip_address in caplog.records[0].message
                            assert "Network Error" in caplog.records[0].message

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(manager, "updateState") as update_state:
            with patch.object(manager, "connect_subscribe") as connect_subscribe:
                connect_subscribe.side_effect = S30Exception("Bad Login", EC_LOGIN, 0)
                with patch("asyncio.create_task") as create_task:
                    ex: HomeAssistantError = None
                    try:
                        await manager.reinitialize_task()
                    except HomeAssistantError as hae:
                        ex = hae
                    assert ex is not None
                    assert "unable to login" in str(ex)
                    assert manager._ip_address in str(ex)

                    assert connect_subscribe.call_count == 1
                    assert len(connect_subscribe.mock_calls[0].args) == 0
                    assert update_state.call_count == 1
                    assert update_state.mock_calls[0].args[0] == DS_CONNECTING


@pytest.mark.asyncio
async def test_manager_messagePump_task(manager_us_customary_units: Manager, caplog):
    manager = manager_us_customary_units
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.return_value = True
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = False
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, True, True]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 1
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval

                                        assert messagePump.call_count == 1
                                        assert len(messagePump.mock_calls[0].args) == 0

                                        assert event_wait_mp_wakeup.call_count == 0

                                        assert update_cloud_presence.call_count == 0

                                        assert update_state.call_count == 1
                                        assert update_state.mock_calls[0].args[0] == DS_DISCONNECTED

                                        assert create_task.call_count == 1
                                        assert reinitialize_task.call_count == 1

                                        assert len(caplog.records) == 1
                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "is exiting - to enter retries" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message

    manager.api.isLANConnection = False
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.return_value = True
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = False
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, True, True]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 1
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval

                                        assert messagePump.call_count == 1
                                        assert len(messagePump.mock_calls[0].args) == 0

                                        assert event_wait_mp_wakeup.call_count == 0

                                        assert update_cloud_presence.call_count == 1
                                        assert len(update_cloud_presence.mock_calls[0].args) == 0

                                        assert update_state.call_count == 1
                                        assert update_state.mock_calls[0].args[0] == DS_DISCONNECTED

                                        assert create_task.call_count == 1
                                        assert reinitialize_task.call_count == 1

                                        assert len(caplog.records) == 1
                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "is exiting - to enter retries" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message

    manager.api.isLANConnection = True
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.return_value = False
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = False
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, True, True]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 1
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval

                                        assert messagePump.call_count == 1
                                        assert len(messagePump.mock_calls[0].args) == 0

                                        assert event_wait_mp_wakeup.call_count == 1
                                        assert event_wait_mp_wakeup.mock_calls[0].args[0] == manager._poll_interval

                                        assert update_cloud_presence.call_count == 0

                                        assert update_state.call_count == 1
                                        assert update_state.mock_calls[0].args[0] == DS_DISCONNECTED

                                        assert create_task.call_count == 1
                                        assert reinitialize_task.call_count == 1

                                        assert len(caplog.records) == 1
                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "is exiting - to enter retries" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message

    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.return_value = False
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = True
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, False, True, True]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 2
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval
                                        assert sleep.mock_calls[1].args[0] == manager._fast_poll_interval

                                        assert messagePump.call_count == 2
                                        assert len(messagePump.mock_calls[0].args) == 0
                                        assert len(messagePump.mock_calls[1].args) == 0

                                        assert event_wait_mp_wakeup.call_count == 1
                                        assert event_wait_mp_wakeup.mock_calls[0].args[0] == manager._poll_interval

                                        assert update_cloud_presence.call_count == 0

                                        assert update_state.call_count == 1
                                        assert update_state.mock_calls[0].args[0] == DS_DISCONNECTED

                                        assert create_task.call_count == 1
                                        assert reinitialize_task.call_count == 1

                                        assert len(caplog.records) == 1

                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "is exiting - to enter retries" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message

    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.side_effect = S30Exception("Network Error", EC_COMMS_ERROR, 0)
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = True
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, True, True]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 1
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval

                                        assert messagePump.call_count == 1
                                        assert len(messagePump.mock_calls[0].args) == 0

                                        assert event_wait_mp_wakeup.call_count == 1
                                        assert event_wait_mp_wakeup.mock_calls[0].args[0] == manager._poll_interval

                                        assert update_cloud_presence.call_count == 0

                                        assert update_state.call_count == 1
                                        assert update_state.mock_calls[0].args[0] == DS_DISCONNECTED

                                        assert create_task.call_count == 1
                                        assert reinitialize_task.call_count == 1

                                        assert len(caplog.records) == 2
                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "unexpected exception" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message

                                        assert "messagePump_task host" in caplog.records[1].message
                                        assert "is exiting - to enter retries" in caplog.records[1].message
                                        assert manager._ip_address in caplog.records[1].message

    with caplog.at_level(logging.DEBUG):
        manager._shutdown = True
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.return_value = True
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = False
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, True, True]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 1
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval

                                        assert messagePump.call_count == 1
                                        assert len(messagePump.mock_calls[0].args) == 0

                                        assert event_wait_mp_wakeup.call_count == 0

                                        assert update_cloud_presence.call_count == 0

                                        assert update_state.call_count == 0

                                        assert create_task.call_count == 0
                                        assert reinitialize_task.call_count == 0

                                        assert len(caplog.records) == 1
                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "is exiting to shutdown" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message

    manager._shutdown = False

    manager._fast_poll_count = 5
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.return_value = False
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = True
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, False, False, False, False, False, True, True]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 5
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval
                                        assert sleep.mock_calls[1].args[0] == manager._fast_poll_interval
                                        assert sleep.mock_calls[2].args[0] == manager._fast_poll_interval
                                        assert sleep.mock_calls[3].args[0] == manager._fast_poll_interval
                                        assert sleep.mock_calls[4].args[0] == manager._fast_poll_interval

                                        assert messagePump.call_count == 6

                                        assert event_wait_mp_wakeup.call_count == 2
                                        assert event_wait_mp_wakeup.mock_calls[0].args[0] == manager._poll_interval
                                        assert event_wait_mp_wakeup.mock_calls[1].args[0] == manager._poll_interval

                                        assert update_cloud_presence.call_count == 0

                                        assert update_state.call_count == 1
                                        assert update_state.mock_calls[0].args[0] == DS_DISCONNECTED

                                        assert create_task.call_count == 1
                                        assert reinitialize_task.call_count == 1

                                        assert len(caplog.records) == 1

                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "is exiting - to enter retries" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch("asyncio.sleep") as sleep:
            with patch.object(manager, "messagePump") as messagePump:
                messagePump.return_value = True
                with patch.object(manager, "update_cloud_presence") as update_cloud_presence:
                    with patch.object(manager, "event_wait_mp_wakeup") as event_wait_mp_wakeup:
                        event_wait_mp_wakeup.return_value = False
                        with patch.object(manager, "get_reinitialize") as get_reinitialize:
                            get_reinitialize.side_effect = [False, True, False]
                            with patch.object(manager, "reinitialize_task") as reinitialize_task:
                                with patch("asyncio.create_task") as create_task:
                                    with patch.object(manager, "updateState") as update_state:
                                        await manager.messagePump_task()
                                        assert sleep.call_count == 1
                                        assert sleep.mock_calls[0].args[0] == manager._poll_interval

                                        assert messagePump.call_count == 1
                                        assert len(messagePump.mock_calls[0].args) == 0

                                        assert event_wait_mp_wakeup.call_count == 0
                                        assert update_cloud_presence.call_count == 0
                                        assert update_state.call_count == 0
                                        assert create_task.call_count == 0
                                        assert reinitialize_task.call_count == 0

                                        assert len(caplog.records) == 1
                                        assert "messagePump_task host" in caplog.records[0].message
                                        assert "is exiting - and this should not happen" in caplog.records[0].message
                                        assert manager._ip_address in caplog.records[0].message


@pytest.mark.asyncio
async def test_manager_messagePump(manager_us_customary_units: Manager, caplog):
    manager = manager_us_customary_units
    manager._err_cnt = 1
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch.object(manager.api, "messagePump") as messagePump:
            messagePump.return_value = True
            with patch.object(manager, "updateState") as update_state:
                res = await manager.messagePump()
                assert res is True

                assert messagePump.call_count == 1
                assert len(messagePump.mock_calls[0].args) == 0

                assert update_state.call_count == 1
                assert update_state.mock_calls[0].args[0] == DS_CONNECTED

                assert len(caplog.records) == 1
                assert "messagePump host" in caplog.records[0].message
                assert "running" in caplog.records[0].message
                assert manager._ip_address in caplog.records[0].message

                assert manager._err_cnt == 0

    manager._reinitialize = False
    manager._err_cnt = 0
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch.object(manager.api, "messagePump") as messagePump:
            messagePump.side_effect = S30Exception("Unauthorized", EC_UNAUTHORIZED, 0)
            with patch.object(manager, "updateState") as update_state:
                res = await manager.messagePump()
                assert res is False
                assert manager._err_cnt == 1
                assert manager._reinitialize is True

                assert messagePump.call_count == 1
                assert len(messagePump.mock_calls[0].args) == 0

                assert update_state.call_count == 0

                assert len(caplog.records) == 1
                assert "messagePump host" in caplog.records[0].message
                assert "unauthorized - trying to relogin" in caplog.records[0].message
                assert manager._ip_address in caplog.records[0].message

    manager._reinitialize = False
    manager._err_cnt = 0
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        with patch.object(manager.api, "messagePump") as messagePump:
            messagePump.side_effect = S30Exception("Http Error", EC_HTTP_ERR, 0)
            with patch.object(manager, "updateState") as update_state:
                res = await manager.messagePump()
                assert res is False
                assert manager._err_cnt == 1
                assert manager._reinitialize is False

                assert messagePump.call_count == 1
                assert update_state.call_count == 0

                assert len(caplog.records) == 2
                assert "messagePump http error host" in caplog.records[1].message
                assert "Http Error" in caplog.records[1].message
                assert manager._ip_address in caplog.records[1].message

    manager._reinitialize = False
    manager._err_cnt = 0
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        with patch.object(manager.api, "messagePump") as messagePump:
            messagePump.side_effect = S30Exception("Network Error", EC_COMMS_ERROR, 0)
            with patch.object(manager, "updateState") as update_state:
                res = await manager.messagePump()
                assert res is False
                assert manager._err_cnt == 1
                assert manager._reinitialize is False

                assert messagePump.call_count == 1
                assert update_state.call_count == 0

                assert len(caplog.records) == 1
                assert "messagePump communication error host" in caplog.records[0].message
                assert "Network Error" in caplog.records[0].message
                assert manager._ip_address in caplog.records[0].message

    manager._reinitialize = False
    manager._err_cnt = 2
    with caplog.at_level(logging.INFO):
        caplog.clear()
        with patch.object(manager.api, "messagePump") as messagePump:
            messagePump.side_effect = S30Exception("Http Error", EC_HTTP_ERR, 0)
            with patch.object(manager, "updateState") as update_state:
                res = await manager.messagePump()
                assert res is False
                assert manager._err_cnt == 3
                assert manager._reinitialize is True

                assert messagePump.call_count == 1
                assert update_state.call_count == 0

                assert len(caplog.records) == 2
                assert "messagePump error host" in caplog.records[0].message
                assert "Http Error" in caplog.records[0].message
                assert manager._ip_address in caplog.records[0].message

                assert "messagePump encountered [3] consecutive errors" in caplog.records[1].message
                assert manager._ip_address in caplog.records[1].message

    manager._reinitialize = False
    manager._err_cnt = 0
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(manager.api, "messagePump") as messagePump:
            messagePump.side_effect = ValueError("Value Error")
            with patch.object(manager, "updateState") as update_state:
                res = await manager.messagePump()
                assert res is False
                assert manager._err_cnt == 1
                assert manager._reinitialize is False

                assert messagePump.call_count == 1
                assert update_state.call_count == 0

                assert len(caplog.records) == 1
                assert "messagePump unexpected exception host" in caplog.records[0].message
                assert manager._ip_address in caplog.records[0].message


@pytest.mark.asyncio
async def test_manager_get_reinitialize(manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    manager._reinitialize = False
    assert manager.get_reinitialize() is False
    manager._reinitialize = True
    assert manager.get_reinitialize() is True


@pytest.mark.asyncio
async def test_manager_async_shutdown_s30_initialize(manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    manager._climate_entities_initialized = True
    with patch.object(manager, "messagePump") as messagePump, patch.object(manager, "connect_subscribe"), patch.object(
        manager, "configuration_initialization"
    ), patch.object(manager.api, "shutdown"):
        messagePump.return_value = False

        await manager.s30_initialize()
        ex: asyncio.TimeoutError = None
        # First make sure the retrieve task is actually running
        assert manager._retrieve_task is not None
        assert manager._retrieve_task.done() is False

        shutdown = manager.async_shutdown(None)
        ex = None
        try:
            await asyncio.wait_for(shutdown, timeout=5)
        except asyncio.TimeoutError as e:
            ex = e
        assert ex is None


@pytest.mark.asyncio
async def test_manager_async_shutdown_reinitialize(manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    manager._climate_entities_initialized = True
    with patch.object(manager, "messagePump") as messagePump, patch.object(manager, "connect_subscribe"), patch.object(
        manager.api, "shutdown"
    ):
        messagePump.return_value = False

        await manager.reinitialize_task()
        ex: asyncio.TimeoutError = None
        # First make sure the retrieve task is actually running
        assert manager._retrieve_task is not None
        assert manager._retrieve_task.done() is False

        shutdown = manager.async_shutdown(None)
        ex = None
        try:
            await asyncio.wait_for(shutdown, timeout=5)
        except asyncio.TimeoutError as e:
            ex = e
        assert ex is None


@pytest.mark.asyncio
async def test_manager_unique_id_update(hass, manager_us_customary_units: Manager):
    manager = manager_us_customary_units
    system = manager.api.system_list[0]
    system.productType = "S40"
    entry_id = manager.config_entry.entry_id

    ent_reg = er.async_get(hass)
    ent_reg.async_get_or_create(
        "switch", LENNOX_DOMAIN, "123_HA", suggested_object_id="away", config_entry=manager.config_entry
    )
    ent_reg.async_get_or_create(
        "sensor", LENNOX_DOMAIN, "1234_HA", suggested_object_id="temperature", config_entry=manager.config_entry
    )
    ent_reg.async_get_or_create("sensor", "other_domain", "123_HA", suggested_object_id="humidity")
    ent_reg.async_get_or_create(
        "climate", LENNOX_DOMAIN, "123_CL_ZONE1", suggested_object_id="zone1", config_entry=manager.config_entry
    )

    await manager.unique_id_updates()

    assert ent_reg.async_get("switch.away").unique_id == f"{system.unique_id}_HA".replace("-", "")
    assert ent_reg.async_get("sensor.temperature").unique_id == "1234_HA"
    assert ent_reg.async_get("sensor.humidity").unique_id == "123_HA"
    assert ent_reg.async_get("climate.zone1").unique_id == f"{system.unique_id}_CL_ZONE1".replace("-", "")

    entry_id = manager.config_entry.entry_id

    dev_reg = dr.async_get(hass)
    id1 = dev_reg.async_get_or_create(config_entry_id=entry_id, name="S30", identifiers={("lennoxs30", "123")}).id
    id2 = dev_reg.async_get_or_create(
        config_entry_id=entry_id, name="Indoor Unit", identifiers={("lennoxs30", "123_iu")}
    ).id
    id3 = dev_reg.async_get_or_create(
        config_entry_id=entry_id, name="Outdoor Unit", identifiers={("lennoxs30", "1234_ou")}
    ).id
    id4 = dev_reg.async_get_or_create(config_entry_id="12345", name="Other", identifiers={("other", "123")}).id

    await manager.unique_id_updates()

    entry = dev_reg.async_get(id1)
    unique_id = None
    for unique_id in entry.identifiers:
        break
    assert unique_id[1] == system.unique_id.replace("-", "")

    entry = dev_reg.async_get(id2)
    for unique_id in entry.identifiers:
        break
    assert unique_id[1] == f"{system.unique_id}_iu".replace("-", "")

    entry = dev_reg.async_get(id3)
    for unique_id in entry.identifiers:
        break
    assert unique_id[1] == "1234_ou"

    entry = dev_reg.async_get(id4)
    for unique_id in entry.identifiers:
        break
    assert unique_id[1] == "123"


@pytest.mark.asyncio
async def test_manager_unique_id_update_nop(manager_us_customary_units: Manager):
    manager = manager_us_customary_units

    with patch.object(manager, "_update_device_unique_ids") as patch_update_device_unique_ids, patch.object(
        manager, "_update_entity_unique_ids"
    ) as patch__update_entity_unique_ids:
        await manager.unique_id_updates()
        assert patch_update_device_unique_ids.call_count == 0
        assert patch__update_entity_unique_ids.call_count == 0

    system = manager.api.system_list[0]
    system.productType = "S40"
    manager.api.isLANConnection = False
    with patch.object(manager, "_update_device_unique_ids") as patch_update_device_unique_ids, patch.object(
        manager, "_update_entity_unique_ids"
    ) as patch__update_entity_unique_ids:
        await manager.unique_id_updates()
        assert patch_update_device_unique_ids.call_count == 0
        assert patch__update_entity_unique_ids.call_count == 0


@pytest.mark.asyncio
async def test_manager_unique_id_update_errors(manager_us_customary_units: Manager, caplog):
    manager = manager_us_customary_units
    system = manager.api.system_list[0]
    system.productType = "S40"
    with caplog.at_level(logging.ERROR), patch.object(
        manager, "_update_device_unique_ids"
    ) as patch_update_device_unique_ids, patch.object(
        manager, "_update_entity_unique_ids"
    ) as patch__update_entity_unique_ids:
        caplog.clear()
        patch__update_entity_unique_ids.side_effect = KeyError("this is the error")
        await manager.unique_id_updates()
        assert patch_update_device_unique_ids.call_count == 1
        assert patch__update_entity_unique_ids.call_count == 1

        assert len(caplog.messages) == 1
        assert "this is the error" in caplog.messages[0]
        assert "Failed to update entity unique_ids" in caplog.messages[0]

    with caplog.at_level(logging.ERROR), patch.object(
        manager, "_update_device_unique_ids"
    ) as patch_update_device_unique_ids, patch.object(
        manager, "_update_entity_unique_ids"
    ) as patch_update_entity_unique_ids:
        caplog.clear()
        patch_update_device_unique_ids.side_effect = KeyError("this is the error")
        await manager.unique_id_updates()
        assert patch_update_device_unique_ids.call_count == 1
        assert patch_update_entity_unique_ids.call_count == 1

        assert len(caplog.messages) == 1
        assert "this is the error" in caplog.messages[0]
        assert "Failed to update device unique_ids" in caplog.messages[0]


# There are problems with Event Loops that makes this test fail.  Needs fixing.
# @pytest.mark.asyncio
# async def test_manager_event_wait_mp_wakeup(manager_us_customary_units: Manager, caplog):
#    loop = asyncio.get_event_loop()
#    manager = manager_us_customary_units
#    res = await manager.event_wait_mp_wakeup(1.0)
#    assert res == False
#
#    manager.mp_wakeup_event.set()
#    res = await manager.event_wait_mp_wakeup(2.0)
#    assert res == True
