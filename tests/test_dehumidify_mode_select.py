# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
from unittest.mock import patch
import pytest

from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import (
    LENNOX_DEHUMIDIFICATION_MODE_HIGH,
    LENNOX_DEHUMIDIFICATION_MODE_MEDIUM,
    LENNOX_DEHUMIDIFICATION_MODE_AUTO,
    lennox_system,
)


from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.select import DehumidificationModeSelect
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from tests.conftest import (
    conf_test_exception_handling,
    conftest_base_entity_availability,
    conf_test_select_info_async_select_option,
)


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)
    assert c.unique_id == system.unique_id + "_DHMS"


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)
    assert c.name == system.name + "_dehumidification_mode"


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_current_option(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)

    assert system.dehumidificationMode == LENNOX_DEHUMIDIFICATION_MODE_AUTO
    assert c.current_option == "climate IQ"
    assert c.available is True

    system.dehumidificationMode = LENNOX_DEHUMIDIFICATION_MODE_HIGH
    assert c.current_option == "max"
    assert c.available is True

    system.dehumidificationMode = LENNOX_DEHUMIDIFICATION_MODE_MEDIUM
    assert c.current_option == "normal"
    assert c.available is True

    system.dehumidificationMode = "UNKNOWN MODE"
    assert c.current_option is None
    assert c.available is True


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_subscription(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    system.dehumidificationMode = None
    c = DehumidificationModeSelect(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"dehumidificationMode": LENNOX_DEHUMIDIFICATION_MODE_HIGH}
        system.attr_updater(update_set, "dehumidificationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == "max"
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"dehumidificationMode": LENNOX_DEHUMIDIFICATION_MODE_MEDIUM}
        system.attr_updater(update_set, "dehumidificationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == "normal"
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"dehumidificationMode": LENNOX_DEHUMIDIFICATION_MODE_AUTO}
        system.attr_updater(update_set, "dehumidificationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == "climate IQ"
        assert c.available is True

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_options(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)

    opt = c.options
    assert len(opt) == 3
    assert "normal" in opt
    assert "max" in opt
    assert "climate IQ" in opt


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
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
        with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
            ex: HomeAssistantError = None
            try:
                await c.async_select_option("bad_value")
            except HomeAssistantError as err:
                ex = err
            assert ex is not None
            assert set_dehumidificationMode.call_count == 0
            msg = str(ex)
            assert "bad_value" in msg
            assert "max" in msg
            assert "normal" in msg
            assert "climate IQ" in msg

    await conf_test_exception_handling(system, "set_dehumidificationMode", c, c.async_select_option, option="normal")
    await conf_test_select_info_async_select_option(system, "set_dehumidificationMode", c, caplog)


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_device_info(hass, manager_mz: Manager):
    manager = manager_mz
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id
