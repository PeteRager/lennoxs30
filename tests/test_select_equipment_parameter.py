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

from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.select import EquipmentParameterSelect


from tests.conftest import (
    conf_test_exception_handling,
    conftest_base_entity_availability,
    conftest_parameter_extra_attributes,
)


@pytest.mark.asyncio
async def test_equipment_parameter_select_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    assert c.unique_id == f"{system.unique_id}_EPS_{equipment.equipment_id}_{parameter.pid}".replace("-", "")


@pytest.mark.asyncio
async def test_equipment_parameter_select_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    assert c.name == "South_Moetown_par_Smooth_Setback_Recovery"


@pytest.mark.asyncio
async def test_equipment_parameter_select_current_option(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    assert parameter.value == "1"
    assert c.current_option == "Enabled"
    assert c.available is True

    parameter.value = "0"
    assert c.current_option == "Disabled"
    assert c.available is True

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        parameter.value = "2"
        assert c.current_option is None
        assert c.available is True
        assert len(caplog.records) == 1
        assert "EquipmentParameterSelect unable to find current radio option value" in caplog.messages[0]
        assert parameter.value in caplog.messages[0]
        assert str(parameter.pid) in caplog.messages[0]
        assert "Enabled" in caplog.messages[0]
        assert "Disabled" in caplog.messages[0]


@pytest.mark.asyncio
async def test_equipment_parameter_select_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        system.executeOnUpdateCallbacksEqParameters("0_130")
        assert update_callback.call_count == 1
        assert c.available is True

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_equipment_parameter_select_options(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    opt = c.options
    assert len(opt) == 2
    assert "Enabled" in opt
    assert "Disabled" in opt


@pytest.mark.asyncio
async def test_equipment_parameter_select_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        await c.async_select_option("Enabled")
        assert set_equipment_parameter_value.call_count == 1
        assert set_equipment_parameter_value.await_args[0][0] == equipment.equipment_id
        assert set_equipment_parameter_value.await_args[0][1] == parameter.pid
        assert set_equipment_parameter_value.await_args[0][2] == "Enabled"

    manager.parameter_safety_turn_on(system.sysId)
    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        ex: HomeAssistantError = None
        try:
            await c.async_select_option("Enabled")
        except HomeAssistantError as e:
            ex = e
        assert ex is not None
        assert set_equipment_parameter_value.call_count == 0
        s = str(ex)
        assert "Unable to set parameter" in s
        assert c._myname in s
        assert "safety switch is on" in s

    manager.parameter_safety_turn_off(system.sysId)
    with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
        await c.async_select_option("Enabled")
        assert set_equipment_parameter_value.call_count == 1
        assert set_equipment_parameter_value.await_args[0][0] == equipment.equipment_id
        assert set_equipment_parameter_value.await_args[0][1] == parameter.pid
        assert set_equipment_parameter_value.await_args[0][2] == "Enabled"

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "set_equipment_parameter_value") as set_equipment_parameter_value:
            set_equipment_parameter_value.side_effect = ValueError("This is the error")
            ex: HomeAssistantError = None
            try:
                await c.async_select_option("bad_value")
            except HomeAssistantError as err:
                ex = err
            assert set_equipment_parameter_value.call_count == 1
            assert ex is not None
            msg = str(ex)
            assert "bad_value" in msg
            assert "This is the error" in msg
            assert "unexpected" in msg
            assert c.name in msg

    await conf_test_exception_handling(
        system, "set_equipment_parameter_value", c, c.async_select_option, option="bad_value"
    )


@pytest.mark.asyncio
async def test_equipment_parameter_select_device_info(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    await manager.create_devices()
    equipment = system.equipment[0]
    parameter = equipment.parameters[130]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    equipment = system.equipment[2]
    parameter = equipment.parameters[34]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id + "_iu"


def test_equipment_parameter_select_entity_category(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    assert c.entity_category == "config"


def test_equipment_parameter_select_extra_attributes(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    equipment = system.equipment[0]
    parameter = equipment.parameters[72]
    c = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
    ex = c.extra_state_attributes
    conftest_parameter_extra_attributes(ex, equipment, parameter)
