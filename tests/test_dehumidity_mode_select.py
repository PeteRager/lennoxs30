import logging
from lennoxs30api.s30api_async import (
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    LENNOX_DEHUMIDIFICATION_MODE_HIGH,
    LENNOX_DEHUMIDIFICATION_MODE_MEDIUM,
    LENNOX_DEHUMIDIFICATION_MODE_AUTO,
    lennox_system,
    lennox_zone,
    LENNOX_ZONING_MODE_CENTRAL,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest

from custom_components.lennoxs30.select import (
    DehumidificationModeSelect,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DehumidificationModeSelect(hass, manager, system)
    assert c.unique_id == system.unique_id() + "_DHMS"


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_name(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = DehumidificationModeSelect(hass, manager, system)
    assert c.name == system.name + "_dehumidification_mode"


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_current_option(
    hass, manager_mz: Manager, caplog
):
    manager = manager_mz
    system: lennox_system = manager._api._systemList[0]
    c = DehumidificationModeSelect(hass, manager, system)

    assert system.dehumidificationMode == LENNOX_DEHUMIDIFICATION_MODE_AUTO
    assert c.current_option == "climate IQ"

    system.dehumidificationMode = LENNOX_DEHUMIDIFICATION_MODE_HIGH
    assert c.current_option == "max"

    system.dehumidificationMode = LENNOX_DEHUMIDIFICATION_MODE_MEDIUM
    assert c.current_option == "normal"


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager._api._systemList[0]
    c = DehumidificationModeSelect(hass, manager, system)

    opt = c.options
    assert len(opt) == 3
    assert "normal" in opt
    assert "max" in opt
    assert "climate IQ" in opt


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_async_select_options(
    hass, manager_mz: Manager, caplog
):
    manager = manager_mz
    system: lennox_system = manager._api._systemList[0]
    c = DehumidificationModeSelect(hass, manager, system)

    with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
        await c.async_select_option("climate IQ")
        assert set_dehumidificationMode.call_count == 1
        arg0 = set_dehumidificationMode.await_args[0][0]
        assert arg0 == LENNOX_DEHUMIDIFICATION_MODE_AUTO

    with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
        await c.async_select_option("max")
        assert set_dehumidificationMode.call_count == 1
        arg0 = set_dehumidificationMode.await_args[0][0]
        assert arg0 == LENNOX_DEHUMIDIFICATION_MODE_HIGH

    with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
        await c.async_select_option("normal")
        assert set_dehumidificationMode.call_count == 1
        arg0 = set_dehumidificationMode.await_args[0][0]
        assert arg0 == LENNOX_DEHUMIDIFICATION_MODE_MEDIUM

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(
            system, "set_dehumidificationMode"
        ) as set_dehumidificationMode:
            await c.async_select_option("bad_value")
            assert set_dehumidificationMode.call_count == 0
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "bad_value" in msg
            assert "max" in msg
            assert "normal" in msg
            assert "climate IQ" in msg
