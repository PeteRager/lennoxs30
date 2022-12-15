"""Tests the manager class"""
# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
import time
from unittest.mock import patch
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM, METRIC_SYSTEM

from lennoxs30api.s30api_async import (
    lennox_system,
    S30Exception,
)

from custom_components.lennoxs30 import Manager


@pytest.mark.asyncio
async def test_manager_configuration_initialization_cloud_offline(manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.cloud_status = "offline"
    with caplog.at_level(logging.WARNING):
        with patch.object(manager, "messagePump") as messagePump:
            messagePump.return_value = False
            caplog.clear()
            await manager.configuration_initialization()
            assert len(caplog.records) == 1
            assert system.sysId in caplog.messages[0]
            assert "offline" in caplog.messages[0]


@pytest.mark.asyncio
async def test_manager_configuration_initialization_cloud_online(manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.cloud_status = "online"
    with caplog.at_level(logging.WARNING):
        with patch.object(manager, "messagePump") as messagePump:
            messagePump.return_value = False
            caplog.clear()
            await manager.configuration_initialization()
            assert len(caplog.records) == 0


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
    with caplog.at_level(logging.WARNING):
        with patch.object(system, "update_system_online_cloud") as mock:
            mock.return_value = False
            caplog.clear()
            await manager.update_cloud_presence()
            assert len(caplog.records) == 0
            assert mock.call_count == 1

    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.ERROR):
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                mock.side_effect = S30Exception("simulated error", 100, 1)
                caplog.clear()
                await manager.update_cloud_presence()
                assert mock.call_count == 1
                assert len(caplog.records) == 1
                assert "simulated error" in caplog.messages[0]
                assert "100" in caplog.messages[0]
                assert "update_cloud_presence" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]

    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.ERROR):
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                mock.side_effect = ValueError()
                caplog.clear()
                await manager.update_cloud_presence()
                assert mock.call_count == 1
                assert len(caplog.records) == 1
                assert "unexpected exception" in caplog.messages[0]
                assert "update_cloud_presence" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]

    # Cloud status online -> offline
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.ERROR):
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                caplog.clear()
                system.cloud_status = "online"
                cp = CloudPresence(system)
                mock.side_effect = cp.toggle_cloud_status
                await manager.update_cloud_presence()
                assert system.cloud_status == "offline"
                assert mock.call_count == 1
                assert len(caplog.records) == 1
                assert "cloud status changed to offline for sysId" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]
                assert mock_subscribe.call_count == 0

    # Cloud status offline -> online
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                caplog.clear()
                system.cloud_status = "offline"
                cp = CloudPresence(system)
                mock.side_effect = cp.toggle_cloud_status
                await manager.update_cloud_presence()
                assert system.cloud_status == "online"
                assert mock.call_count == 1
                assert len(caplog.records) == 1
                assert "cloud status changed to online for sysId" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]
                assert mock_subscribe.call_count == 1

    # Cloud status offline -> online, S30exception on resubscribe
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                system.cloud_status = "offline"
                cp = CloudPresence(system)
                mock.side_effect = cp.toggle_cloud_status
                mock_subscribe.side_effect = S30Exception("simulated error", 10, 0)
                await manager.update_cloud_presence()
                assert system.cloud_status == "online"
                assert mock.call_count == 1
                assert mock_subscribe.call_count == 1

                assert len(caplog.records) == 2
                assert "cloud status changed to online for sysId" in caplog.messages[0]
                assert system.sysId in caplog.messages[0]
                assert "update_cloud_presence resubscribe error" in caplog.messages[1]
                assert system.sysId in caplog.messages[1]
                assert manager._reinitialize is True

    # Cloud status offline -> online, exception on resubscribe
    manager.last_cloud_presence_poll = 1
    with caplog.at_level(logging.INFO):
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                system.cloud_status = "offline"
                cp = CloudPresence(system)
                mock.side_effect = cp.toggle_cloud_status
                mock_subscribe.side_effect = ValueError()
                await manager.update_cloud_presence()
                assert system.cloud_status == "online"
                assert mock.call_count == 1
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
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                await manager.update_cloud_presence()
                assert mock.call_count == 0
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
        with patch.object(system, "update_system_online_cloud") as mock:
            with patch.object(manager.api, "subscribe") as mock_subscribe:
                manager._reinitialize = False
                caplog.clear()
                await manager.update_cloud_presence()
                assert mock.call_count == 1
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
