# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch
import logging

import pytest

from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.number import (
    DiagnosticLevelNumber,
)


from tests.conftest import conf_test_exception_handling, conftest_base_entity_availability


@pytest.mark.asyncio
async def test_diagnostic_level_misc(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.should_poll is False
    assert c.update() is True


@pytest.mark.asyncio
async def test_diagnostic_level_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)

    assert c.unique_id == (system.unique_id + "_DL").replace("-", "")


@pytest.mark.asyncio
async def test_diagnostic_level_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)

    assert c.name == system.name + "_diagnostic_level"


@pytest.mark.asyncio
async def test_diagnostic_level_unique_id_unit_of_measure(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.unit_of_measurement is None


@pytest.mark.asyncio
async def test_diagnostic_level_max_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.max_value == 2


@pytest.mark.asyncio
async def test_diagnostic_level_min_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.min_value == 0


@pytest.mark.asyncio
async def test_diagnostic_level_step(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.step == 1


@pytest.mark.asyncio
async def test_diagnostic_level_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)
    assert c.value == system.diagLevel
    assert c.available is True

    system.diagLevel = 2
    assert c.value == 2
    assert c.available is True


@pytest.mark.asyncio
async def test_diagnostic_level_set_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = DiagnosticLevelNumber(hass, manager, system)

    with patch.object(system, "set_diagnostic_level") as set_diagnostic_level:
        await c.async_set_native_value(2)
        assert set_diagnostic_level.call_count == 1
        assert set_diagnostic_level.call_args[0][0] == 2

    system.internetStatus = False
    system.relayServerConnected = False
    with caplog.at_level(logging.WARNING):
        with patch.object(system, "set_diagnostic_level") as set_diagnostic_level:
            caplog.clear()
            await c.async_set_native_value(1)
            assert len(caplog.records) == 1
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[0]
            caplog.clear()
            await c.async_set_native_value(2)
            assert len(caplog.records) == 0
            caplog.clear()
            await c.async_set_native_value(0)
            assert len(caplog.records) == 0

    system.internetStatus = True
    system.relayServerConnected = False
    with caplog.at_level(logging.WARNING):
        with patch.object(system, "set_diagnostic_level") as set_diagnostic_level:
            caplog.clear()
            await c.async_set_native_value(1)
            assert len(caplog.records) == 2
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[0]
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[1]
            caplog.clear()
            await c.async_set_native_value(2)
            assert len(caplog.records) == 1
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[0]
            caplog.clear()
            await c.async_set_native_value(0)
            assert len(caplog.records) == 0

    system.internetStatus = False
    system.relayServerConnected = True
    with caplog.at_level(logging.WARNING):
        with patch.object(system, "set_diagnostic_level") as set_diagnostic_level:
            caplog.clear()
            await c.async_set_native_value(1)
            assert len(caplog.records) == 2
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[0]
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[1]
            caplog.clear()
            await c.async_set_native_value(2)
            assert len(caplog.records) == 1
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[0]
            caplog.clear()
            await c.async_set_native_value(0)
            assert len(caplog.records) == 0

    system.internetStatus = True
    system.relayServerConnected = True
    with caplog.at_level(logging.WARNING):
        with patch.object(system, "set_diagnostic_level") as set_diagnostic_level:
            caplog.clear()
            await c.async_set_native_value(1)
            assert len(caplog.records) == 2
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[0]
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[1]
            caplog.clear()
            await c.async_set_native_value(2)
            assert len(caplog.records) == 1
            assert "https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md" in caplog.messages[0]
            caplog.clear()
            await c.async_set_native_value(0)
            assert len(caplog.records) == 0

    system.internetStatus = False
    system.relayServerConnected = False
    await conf_test_exception_handling(system, "set_diagnostic_level", c, c.async_set_native_value, value=1)


@pytest.mark.asyncio
async def test_diagnostic_level_device_info(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = DiagnosticLevelNumber(hass, manager, system)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id


@pytest.mark.asyncio
async def test_diagnostic_level_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = DiagnosticLevelNumber(hass, manager, system)
    await c.async_added_to_hass()

    system.diagLevel = None
    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {
            "diagLevel": 0,
        }
        system.attr_updater(update_set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {
            "diagLevel": 1,
        }
        system.attr_updater(update_set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {
            "diagLevel": 2,
        }
        system.attr_updater(update_set, "diagLevel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    conftest_base_entity_availability(manager, system, c)
