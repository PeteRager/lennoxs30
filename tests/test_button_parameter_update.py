import logging
from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import Manager
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.button import EquipmentParameterUpdateButton
from homeassistant.exceptions import HomeAssistantError
from lennoxs30api.s30exception import S30Exception

from unittest.mock import patch

from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_button_parameter_update_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = EquipmentParameterUpdateButton(hass, manager, system)
    assert c.unique_id == f"{system.unique_id}_BUT_PU".replace("-", "")


@pytest.mark.asyncio
async def test_button_parameter_update_name(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = EquipmentParameterUpdateButton(hass, manager, system)
    assert c.name == "South Moetown_parameter_update"


@pytest.mark.asyncio
async def test_button_parameter_update_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = EquipmentParameterUpdateButton(hass, manager, system)
    await c.async_added_to_hass()
    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_button_parameter_update_async_press(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = EquipmentParameterUpdateButton(hass, manager, system)

    with patch.object(system, "_internal_set_equipment_parameter_value") as _internal_set_equipment_parameter_value:
        await c.async_press()
        assert _internal_set_equipment_parameter_value.call_count == 1
        assert _internal_set_equipment_parameter_value.await_args[0][0] == 0
        assert _internal_set_equipment_parameter_value.await_args[0][1] == 0
        assert _internal_set_equipment_parameter_value.await_args[0][2] == ""

    manager.parameter_safety_turn_on(system.sysId)
    with patch.object(system, "_internal_set_equipment_parameter_value") as _internal_set_equipment_parameter_value:
        ex: HomeAssistantError = None
        try:
            await c.async_press()
        except HomeAssistantError as e:
            ex = e
        assert ex != None
        assert _internal_set_equipment_parameter_value.call_count == 0
        s = str(ex)
        assert "Unable to parameter update" in s
        assert c._myname in s
        assert "safety switch is on" in s

    manager.parameter_safety_turn_off(system.sysId)
    with patch.object(system, "_internal_set_equipment_parameter_value") as _internal_set_equipment_parameter_value:
        await c.async_press()
        assert _internal_set_equipment_parameter_value.call_count == 1
        assert _internal_set_equipment_parameter_value.await_args[0][0] == 0
        assert _internal_set_equipment_parameter_value.await_args[0][1] == 0
        assert _internal_set_equipment_parameter_value.await_args[0][2] == ""

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "_internal_set_equipment_parameter_value") as _internal_set_equipment_parameter_value:
            caplog.clear()
            _internal_set_equipment_parameter_value.side_effect = S30Exception("This is the error", 100, 200)
            await c.async_press()
            assert len(caplog.records) == 1
            assert "EquipmentParameterUpdateButton::async_press" in caplog.messages[0]
            assert "This is the error" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "_internal_set_equipment_parameter_value") as _internal_set_equipment_parameter_value:
            _internal_set_equipment_parameter_value.side_effect = S30Exception("This is the error", 10, 101)
            await c.async_press()
            assert _internal_set_equipment_parameter_value.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "This is the error" in msg
            assert c.name in msg

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "_internal_set_equipment_parameter_value") as _internal_set_equipment_parameter_value:
            _internal_set_equipment_parameter_value.side_effect = ValueError("This is the error")
            await c.async_press()
            assert _internal_set_equipment_parameter_value.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "This is the error" in msg
            assert "unexpected" in msg
            assert c.name in msg


@pytest.mark.asyncio
async def test_button_parameter_update_device_info(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    await manager.create_devices()
    c = EquipmentParameterUpdateButton(hass, manager, system)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id


def test_button_parameter_update_entity_category(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = EquipmentParameterUpdateButton(hass, manager, system)
    assert c.entity_category == "config"
