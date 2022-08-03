import logging
from lennoxs30api.s30api_async import (
    LENNOX_STATUS_NOT_EXIST,
    LENNOX_STATUS_GOOD,
    LENNOX_VENTILATION_DAMPER,
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import CONF_CLOUD_CONNECTION, MANAGER

from custom_components.lennoxs30.number import (
    DiagnosticLevelNumber,
    DehumidificationOverCooling,
    CirculateTime,
    TimedVentilationNumber,
    async_setup_entry,
)

from unittest.mock import patch, Mock


@pytest.mark.asyncio
async def test_manager_configuration_initialization_cloud_offline(
    hass, manager: Manager, caplog
):
    system: lennox_system = manager._api._systemList[0]
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
async def test_manager_configuration_initialization_cloud_online(
    hass, manager: Manager, caplog
):
    system: lennox_system = manager._api._systemList[0]
    system.cloud_status = "online"
    with caplog.at_level(logging.WARNING):
        with patch.object(manager, "messagePump") as messagePump:
            messagePump.return_value = False
            caplog.clear()
            await manager.configuration_initialization()
            assert len(caplog.records) == 0
