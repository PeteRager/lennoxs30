from hashlib import sha3_224
import logging
from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_RETRY_WAIT,
    Manager,
)
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.number import (
    DiagnosticLevelNumber,
)

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_diagnostic_level_misc(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.should_poll == False
    assert c.update() == True


@pytest.mark.asyncio
async def test_diagnostic_level_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_DL").replace("-", "")


@pytest.mark.asyncio
async def test_diagnostic_level_name(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)

    assert c.name == system.name + "_diagnostic_level"


@pytest.mark.asyncio
async def test_diagnostic_level_unique_id_unit_of_measure(
    hass, manager: Manager, caplog
):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.unit_of_measurement == None


@pytest.mark.asyncio
async def test_diagnostic_level_max_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.max_value == 2


@pytest.mark.asyncio
async def test_diagnostic_level_min_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.min_value == 0


@pytest.mark.asyncio
async def test_diagnostic_level_step(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.step == 1


@pytest.mark.asyncio
async def test_diagnostic_level_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.value == system.diagLevel
    assert c.available == True

    system.diagLevel = 2
    assert c.value == 2
    assert c.available == True


@pytest.mark.asyncio
async def test_diagnostic_level_set_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = True
    c = DiagnosticLevelNumber(hass, manager, system)

    with patch.object(system, "set_diagnostic_level") as set_diagnostic_level:
        await c.async_set_value(2)
        assert set_diagnostic_level.call_count == 1
        assert set_diagnostic_level.call_args[0][0] == 2


@pytest.mark.asyncio
async def test_diagnostic_level_device_info(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = True
    c = DiagnosticLevelNumber(hass, manager, system)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()


@pytest.mark.asyncio
async def test_diagnostic_level_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = True
    c = DiagnosticLevelNumber(hass, manager, system)
    await c.async_added_to_hass()

    system.diagLevel = None
    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "diagLevel": 0,
        }
        system.attr_updater(set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "diagLevel": 1,
        }
        system.attr_updater(set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "diagLevel": 2,
        }
        system.attr_updater(set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False
