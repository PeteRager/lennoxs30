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
    LENNOX_VENTILATION_MODE_OFF,
    LENNOX_VENTILATION_MODE_ON,
    LENNOX_VENTILATION_MODE_INSTALLER,
    LENNOX_VENTILATION_CONTROL_MODE_ASHRAE,
    lennox_system,
)


from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.select import VentilationModeSelect
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from tests.conftest import (
    conf_test_exception_handling,
    conftest_base_entity_availability,
    conf_test_select_info_async_select_option,
)


@pytest.mark.asyncio
async def test_select_ventilation_mode_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = VentilationModeSelect(hass, manager, system)
    assert c.unique_id == system.unique_id + "_VENT_SELECT"


@pytest.mark.asyncio
async def test_select_ventilation_mode_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = VentilationModeSelect(hass, manager, system)
    assert c.name == system.name + "_ventilation_mode"


@pytest.mark.asyncio
async def test_select_ventilation_mode_current_option(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = VentilationModeSelect(hass, manager, system)

    system.ventilationMode = LENNOX_VENTILATION_MODE_INSTALLER
    assert c.current_option == LENNOX_VENTILATION_MODE_INSTALLER
    assert c.available is True
    arr = c.extra_state_attributes
    assert len(arr) == 1
    assert arr["installer_settings"] == system.ventilationControlMode

    system.ventilationMode = LENNOX_VENTILATION_MODE_ON
    assert c.current_option == LENNOX_VENTILATION_MODE_ON
    assert c.available is True

    system.ventilationMode = LENNOX_VENTILATION_MODE_OFF
    assert c.current_option == LENNOX_VENTILATION_MODE_OFF
    assert c.available is True


@pytest.mark.asyncio
async def test_select_ventilation_mode_subscription(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    system.dehumidificationMode = None
    c = VentilationModeSelect(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"ventilationMode": LENNOX_VENTILATION_MODE_OFF}
        system.attr_updater(update_set, "ventilationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_VENTILATION_MODE_OFF
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"ventilationMode": LENNOX_VENTILATION_MODE_ON}
        system.attr_updater(update_set, "ventilationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_VENTILATION_MODE_ON
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"ventilationMode": LENNOX_VENTILATION_MODE_INSTALLER}
        system.attr_updater(update_set, "ventilationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_VENTILATION_MODE_INSTALLER
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"ventilationControlMode": LENNOX_VENTILATION_CONTROL_MODE_ASHRAE}
        system.attr_updater(update_set, "ventilationControlMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.extra_state_attributes["installer_settings"] == LENNOX_VENTILATION_CONTROL_MODE_ASHRAE
        assert c.available is True

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_select_ventilation_mode_options(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = VentilationModeSelect(hass, manager, system)

    opt = c.options
    assert len(opt) == 3
    assert LENNOX_VENTILATION_MODE_INSTALLER in opt
    assert LENNOX_VENTILATION_MODE_ON in opt
    assert LENNOX_VENTILATION_MODE_OFF in opt


@pytest.mark.asyncio
async def test_select_ventilation_mode_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = VentilationModeSelect(hass, manager, system)

    with patch.object(system, "ventilation_on") as set_dehumidificationMode:
        await c.async_select_option(LENNOX_VENTILATION_MODE_ON)
        assert set_dehumidificationMode.call_count == 1

    with patch.object(system, "ventilation_off") as set_dehumidificationMode:
        await c.async_select_option(LENNOX_VENTILATION_MODE_OFF)
        assert set_dehumidificationMode.call_count == 1

    with patch.object(system, "ventilation_installer") as set_dehumidificationMode:
        await c.async_select_option(LENNOX_VENTILATION_MODE_INSTALLER)
        assert set_dehumidificationMode.call_count == 1

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

    await conf_test_exception_handling(
        system, "ventilation_on", c, c.async_select_option, option=LENNOX_VENTILATION_MODE_ON
    )
    await conf_test_select_info_async_select_option(system, "ventilation_on", c, caplog)


@pytest.mark.asyncio
async def test_select_ventilation_mode_device_info(hass, manager_mz: Manager):
    manager = manager_mz
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    c = VentilationModeSelect(hass, manager, system)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id
