"""Test the parameter update button"""
# pylint: disable=protected-access
# pylint: disable=missing-function-docstring

from unittest.mock import patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import (
    lennox_system,
)

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.button import EquipmentParameterUpdateButton


from tests.conftest import conf_test_exception_handling, conftest_base_entity_availability


@pytest.mark.asyncio
async def test_button_parameter_update_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = EquipmentParameterUpdateButton(hass, manager, system)
    assert button.unique_id == f"{system.unique_id}_BUT_PU".replace("-", "")


@pytest.mark.asyncio
async def test_button_parameter_update_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = EquipmentParameterUpdateButton(hass, manager, system)
    assert button.name == "South Moetown_parameter_update"


@pytest.mark.asyncio
async def test_button_parameter_update_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = EquipmentParameterUpdateButton(hass, manager, system)
    await button.async_added_to_hass()
    conftest_base_entity_availability(manager, system, button)


@pytest.mark.asyncio
async def test_button_parameter_update_async_press(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    button = EquipmentParameterUpdateButton(hass, manager, system)

    with patch.object(system, "set_parameter_value") as set_parameter_value:
        await button.async_press()
        assert set_parameter_value.call_count == 1
        assert set_parameter_value.await_args[0][0] == 0
        assert set_parameter_value.await_args[0][1] == 0
        assert set_parameter_value.await_args[0][2] == ""

    manager.parameter_safety_turn_on(system.sysId)
    with patch.object(system, "set_parameter_value") as set_parameter_value:
        ex: HomeAssistantError = None
        try:
            await button.async_press()
        except HomeAssistantError as h_e:
            ex = h_e
        assert ex is not None
        assert set_parameter_value.call_count == 0
        assert "Unable to parameter update" in str(ex)
        assert button._myname in str(ex)
        assert "safety switch is on" in str(ex)

    manager.parameter_safety_turn_off(system.sysId)
    with patch.object(system, "set_parameter_value") as set_parameter_value:
        await button.async_press()
        assert set_parameter_value.call_count == 1
        assert set_parameter_value.await_args[0][0] == 0
        assert set_parameter_value.await_args[0][1] == 0
        assert set_parameter_value.await_args[0][2] == ""

    await conf_test_exception_handling(system, "set_parameter_value", button, button.async_press)


@pytest.mark.asyncio
async def test_button_parameter_update_device_info(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    await manager.create_devices()
    button = EquipmentParameterUpdateButton(hass, manager, system)

    identifiers = button.device_info["identifiers"]
    for ids in identifiers:
        assert ids[0] == LENNOX_DOMAIN
        assert ids[1] == system.unique_id


def test_button_parameter_update_entity_category(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    button = EquipmentParameterUpdateButton(hass, manager, system)
    assert button.entity_category == "config"
